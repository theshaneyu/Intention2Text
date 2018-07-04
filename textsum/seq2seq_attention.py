"""Trains a seq2seq model.
實作 "Abstractive Text Summarization using Sequence-to-sequence RNNS and Beyond."
"""

"""
每次更改要注意的參數：
CUDA_VISIBLE_DEVICES
eval_interval_secs
per_process_gpu_memory_fraction
模型參數區
"""
import sys
import time

import tensorflow as tf
import batch_reader
import data
import seq2seq_attention_decode
import seq2seq_attention_model
import os


from tensorflow.contrib.tensorboard.plugins import projector
from data_convert_example import text_to_binary
from gen_user_input_for_decoding import preprocessing
from pprint import pprint


os.environ["CUDA_VISIBLE_DEVICES"] = '0' # 指定使用某顆GPU跑


FLAGS = tf.app.flags.FLAGS
tf.app.flags.DEFINE_string('data_path', '', 'Path expression to tf.Example.')
tf.app.flags.DEFINE_string('vocab_path',
                           '', 'Path expression to text vocabulary file.')
tf.app.flags.DEFINE_string('article_key', 'context',
                           'tf.Example feature key for article.')
tf.app.flags.DEFINE_string('abstract_key', 'description',
                           'tf.Example feature key for abstract.')
tf.app.flags.DEFINE_string('log_root', '', 'Directory for model root.')
tf.app.flags.DEFINE_string('train_dir', '', 'Directory for train.')
tf.app.flags.DEFINE_string('eval_dir', '', 'Directory for eval.')
tf.app.flags.DEFINE_string('decode_dir', '', 'Directory for decode summaries.')
tf.app.flags.DEFINE_string('mode', 'train', 'train/eval/decode mode')
tf.app.flags.DEFINE_integer('max_run_steps', 100000000,
                            'Maximum number of run steps.')
tf.app.flags.DEFINE_integer('max_article_sentences', 2,
                            'Max number of first sentences to use from the '
                            'article')
tf.app.flags.DEFINE_integer('max_abstract_sentences', 100,
                            'Max number of first sentences to use from the '
                            'abstract')
tf.app.flags.DEFINE_integer('beam_size', 4,
                            'beam size for beam search decoding.')
tf.app.flags.DEFINE_integer('eval_interval_secs', 5, 'How often to run eval.')
tf.app.flags.DEFINE_integer('checkpoint_secs', 60, 'How often to checkpoint.')
tf.app.flags.DEFINE_bool('use_bucketing', False,
                         'Whether bucket articles of similar length.')
tf.app.flags.DEFINE_bool('truncate_input', False,
                         'Truncate inputs that are too long. If False, '
                         'examples that are too long are discarded.')
tf.app.flags.DEFINE_integer('num_gpus', 1, 'Number of gpus used.')
tf.app.flags.DEFINE_integer('random_seed', 111, 'A seed value for randomness.')


def _RunningAvgLoss(loss, running_avg_loss, summary_writer, step, decay=0.999):
    """Calculate the running average of losses."""
    if running_avg_loss == 0:
        running_avg_loss = loss
    else:
        running_avg_loss = running_avg_loss * decay + (1 - decay) * loss
    running_avg_loss = min(running_avg_loss, 12)
    loss_sum = tf.Summary()
    loss_sum.value.add(tag='running_avg_loss', simple_value=running_avg_loss)
    summary_writer.add_summary(loss_sum, step)
    print('running_avg_loss: %f' % running_avg_loss, flush=True)
    return running_avg_loss


def _Train(model, data_batcher):
    """Runs model training."""
    with tf.device('/cpu:0'):
        model.build_graph()
        saver = tf.train.Saver()
        # Train dir is different from log_root to avoid summary directory
        # conflict with Supervisor.
        summary_writer = tf.summary.FileWriter(FLAGS.train_dir)
        sv = tf.train.Supervisor(logdir=FLAGS.log_root,
                                 is_chief=True,
                                 saver=saver,
                                 summary_op=None,
                                 save_summaries_secs=60,
                                 save_model_secs=FLAGS.checkpoint_secs,
                                 global_step=model.global_step)
        
        config = tf.ConfigProto(allow_soft_placement=True)
        config.gpu_options.per_process_gpu_memory_fraction = .3
        
        sess = sv.prepare_or_wait_for_session(config=config)
        running_avg_loss = 0
        step = 0
        
        #####################################################################
        # tensorboard上的projector可視化(不用特別修改路徑，會自動根據vocab_path調整)
        embedding_config = projector.ProjectorConfig()
        embeddingConfig = embedding_config.embeddings.add()
        embeddingConfig.tensor_name = model.embedding_tensors_for_projector.name
        embeddingConfig.metadata_path = '~/Projects/behavior2text/' + FLAGS.vocab_path + '.tsv'
        projector.visualize_embeddings(summary_writer, embedding_config)
        #####################################################################

        while not sv.should_stop() and step < FLAGS.max_run_steps:
            (article_batch, abstract_batch, targets, article_lens, abstract_lens,
             loss_weights, _, _) = data_batcher.NextBatch()
            (_, summaries, loss, train_step) = model.run_train_step(
                    sess, article_batch, abstract_batch, targets, article_lens,
                    abstract_lens, loss_weights)

            summary_writer.add_summary(summaries, train_step)
            running_avg_loss = _RunningAvgLoss(
                    running_avg_loss, loss, summary_writer, train_step)
            step += 1
            print('the %d iteration' % step)
            if step % 100 == 0:
                summary_writer.flush()
        sv.Stop()
        return running_avg_loss


def _Eval(model, data_batcher, vocab=None):
    """Runs model eval."""
    model.build_graph()
    saver = tf.train.Saver()
    summary_writer = tf.summary.FileWriter(FLAGS.eval_dir)
    
    config = tf.ConfigProto(allow_soft_placement=True)
    config.gpu_options.per_process_gpu_memory_fraction = .2
    
    sess = tf.Session(config=config)
    running_avg_loss = 0
    step = 0
    while True:
        time.sleep(FLAGS.eval_interval_secs)
        try:
            ckpt_state = tf.train.get_checkpoint_state(FLAGS.log_root)
        except tf.errors.OutOfRangeError as e:
            tf.logging.error('Cannot restore checkpoint: %s', e)
            continue

        if not (ckpt_state and ckpt_state.model_checkpoint_path):
            tf.logging.info('No model to eval yet at %s', FLAGS.train_dir)
            continue

        tf.logging.info('Loading checkpoint %s', ckpt_state.model_checkpoint_path)
        saver.restore(sess, ckpt_state.model_checkpoint_path)

        (article_batch, abstract_batch, targets, article_lens, abstract_lens,
         loss_weights, _, _) = data_batcher.NextBatch()
        (summaries, loss, train_step) = model.run_eval_step(
                sess, article_batch, abstract_batch, targets, article_lens,
                abstract_lens, loss_weights)
        tf.logging.info(
                'article:  %s',
                ' '.join(data.Ids2Words(article_batch[0][:].tolist(), vocab)))
        tf.logging.info(
                'abstract: %s',
                ' '.join(data.Ids2Words(abstract_batch[0][:].tolist(), vocab)))

        summary_writer.add_summary(summaries, train_step)
        running_avg_loss = _RunningAvgLoss(
                running_avg_loss, loss, summary_writer, train_step)
        if step % 100 == 0:
            summary_writer.flush()


def main(unused_argv):
    vocab = data.Vocab(FLAGS.vocab_path, 1000000)
    # Check for presence of required special tokens.
    assert vocab.CheckVocab(data.PAD_TOKEN) > 0
    assert vocab.CheckVocab(data.UNKNOWN_TOKEN) >= 0
    assert vocab.CheckVocab(data.SENTENCE_START) > 0
    assert vocab.CheckVocab(data.SENTENCE_END) > 0

    batch_size = 4
    if FLAGS.mode == 'decode':
        batch_size = FLAGS.beam_size

    hps = seq2seq_attention_model.HParams(
                        mode=FLAGS.mode,  # train, eval, decode
                        min_lr=0.01,  # min learning rate.
                        lr=0.15,  # learning rate
                        batch_size=batch_size,
                        enc_layers=2,
                        enc_timesteps=120,
                        dec_timesteps=30,
                        min_input_len=2,  # discard articles/summaries < than this
                        num_hidden=128,  # for rnn cell
                        emb_dim=128,  # If 0, don't use embedding
                        max_grad_norm=2,
                        num_softmax_samples=4096)  # If 0, no sampled softmax.

    batcher = batch_reader.Batcher(
        FLAGS.data_path, vocab, hps, FLAGS.article_key,
        FLAGS.abstract_key, FLAGS.max_article_sentences,
        FLAGS.max_abstract_sentences, bucketing=FLAGS.use_bucketing,
        truncate_input=FLAGS.truncate_input)
    tf.set_random_seed(FLAGS.random_seed)

    if hps.mode == 'train':
        model = seq2seq_attention_model.Seq2SeqAttentionModel(
            hps, vocab, num_gpus=FLAGS.num_gpus)
        _Train(model, batcher)
    elif hps.mode == 'eval':
        model = seq2seq_attention_model.Seq2SeqAttentionModel(
            hps, vocab, num_gpus=FLAGS.num_gpus)
        _Eval(model, batcher, vocab=vocab)
    elif hps.mode == 'decode':
        decode_mdl_hps = hps
        # Only need to restore the 1st step and reuse it since
        # we keep and feed in state for each step's output.
        decode_mdl_hps = hps._replace(dec_timesteps=1)
        model = seq2seq_attention_model.Seq2SeqAttentionModel(
                decode_mdl_hps, vocab, num_gpus=FLAGS.num_gpus)

        to_build_grapth = True
        p = preprocessing(FLAGS.vocab_path)
        
        # 舊的decode迴圈
        # while True:
        #     kb_input = input('> ')
        #     if kb_input == 'c':
        #         description_str = input('輸入description > ')
        #         context_str = input('輸入context> ')
        #         input_data = p.get_data(description=description_str, context=context_str)
        #         print('輸入資料：')
        #         pprint(input_data)
        #     elif kb_input == 'q':
        #         break
        #     else:
        #         try:
        #             text_to_binary('yahoo_knowledge_data/decode/ver_5/dataset_ready/data_ready_' + kb_input,
        #                     'yahoo_knowledge_data/decode/decode_data')
        #         except:
        #             print('預設testing data出現錯誤')
        #     decoder = seq2seq_attention_decode.BSDecoder(model, hps, vocab, to_build_grapth)
        #     to_build_grapth = False
        #     decoder.DecodeLoop()

        # 論文用的decode迴圈
        file_num = 61
        while True:
            if file_num % 60 == 0:
                break
            try:
                text_to_binary('yahoo_knowledge_data/decode/ver_5/dataset_ready/data_ready_' + str(file_num),
                        'yahoo_knowledge_data/decode/decode_data')
            except:
                print('預設testing data出現錯誤')
                break
            decoder = seq2seq_attention_decode.BSDecoder(model, hps, vocab, to_build_grapth)
            to_build_grapth = False
            decoder.DecodeLoop()
            print('==================', file_num, '==================')
            file_num += 1
            



if __name__ == '__main__':
    tf.app.run()
