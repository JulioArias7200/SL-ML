from flask import Blueprint, render_template, request
from modules.services.nlp_topics_service import NLPTopicsService

nlp_topics_bp = Blueprint('nlp_topics_bp', __name__)

@nlp_topics_bp.route('/nlp-topicos')
def view():
    ctx = request.args.get('ctx', 'bolivia').lower()
    if ctx not in ('bolivia', 'chicago'):
        ctx = 'bolivia'

    summary = NLPTopicsService.get_corpus_summary(ctx)

    return render_template(
        'views/nlp_topicos_lda.html',
        active_page='nlp-topicos',
        current_context=ctx,
        context_title=summary['context_title'],
        source_badge=summary['source_badge'],
        topics=summary['topics'],
        topic_distribution=summary['topic_distribution'],
        sample_notes=summary['sample_notes'],
        total_notes=summary['total_notes'],
        kpis=summary['kpis'],
        presets=summary['presets']
    )
