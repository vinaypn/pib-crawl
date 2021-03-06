from io import StringIO
from bleualign.align import Aligner
from ilmulti.utils.language_utils import inject_token

class BLEUAligner:
    def __init__(self, model, tokenizer, segmenter):
        self.model = model
        self.tokenizer = tokenizer
        self.segmenter = segmenter


    def __call__(self, src, src_lang, tgt, tgt_lang, galechurch=False):
        """
            Input: Paragraphs in two languages and their language codes.
            Output: Obtained parallel sentences using BLEUAlign

        """
        def create_stringio(lines, lang):
            tokenized = [ ' '.join(self.tokenizer(line, lang=lang)[1]) \
                    for line in lines ]
            lstring = '\n'.join(tokenized)
            return tokenized, StringIO(lstring)

        def process(content, lang):
            lang, segments = self.segmenter(content, lang=lang)
            tokenized, _io = create_stringio(segments, lang)
            return tokenized, _io

        src_tokenized, src_io = process(src, src_lang)
        tgt_tokenized, tgt_io = process(tgt, tgt_lang)
        
        print('using galechurch:', galechurch)
        if galechurch==True:
            src, tgt = self.bleu_align(src_io, tgt_io, hyp_src_tgt_file=None)
            return ([], []) , (src, tgt)

        # Inject tokens into src_tokenized
        injected_src_tokenized = inject_token(src_tokenized,tgt_lang)

        generation_output = self.model(injected_src_tokenized)
        hyps = [ gout['tgt'] for gout in generation_output ]
        hyp_io = StringIO('\n'.join(hyps))

        src, tgt = self.bleu_align(src_io, tgt_io, hyp_io)

        return (src_tokenized, hyps), (src, tgt) 



    def bleu_align(self, srcfile, tgtfile, hyp_src_tgt_file=None):
        output = StringIO()
        # src_out, tgt_out = StringIO(), StringIO()
        options = {
            'srcfile': srcfile,
            'targetfile': tgtfile,
            'galechurch' : True if hyp_src_tgt_file is None else False,
            'no_translation_override':True if hyp_src_tgt_file is None else False,
            #'bleu_ngrams' : 4,
            'srctotarget': [hyp_src_tgt_file] if hyp_src_tgt_file else [],
            'targettosrc': [],
            'verbosity' : 0,
            # 'output': output,
            # 'output-src': src_out, 'output-target': tgt_out,
	   }
        a = Aligner(options)
        a.mainloop()
        src_out, tgt_out = a.results()

        srcs = src_out.getvalue().splitlines()
        tgts = tgt_out.getvalue().splitlines()

        return srcs, tgts

    def detok(self, src_out):
        src = []
        for line in src_out:
            src_detok = self.tokenizer.detokenize(line)
            src.append(src_detok)
        return src