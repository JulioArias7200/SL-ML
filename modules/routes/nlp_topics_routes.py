from flask import Blueprint, render_template
from modules.services.bolivia_service import BoliviaService

nlp_topics_bp = Blueprint('nlp_topics_bp', __name__)

@nlp_topics_bp.route('/nlp-topicos')
def view():
    topics = BoliviaService.LDA_TOPICS
    df_nlp = BoliviaService.get_nlp_data()
    
    # Muestra representativa de notas por tópico
    sample_notes = []
    if not df_nlp.empty:
        for row in df_nlp.head(15).itertuples():
            sample_notes.append({
                "titulo": str(row.titulo),
                "delito": str(row.delito_principal),
                "ciudad": str(row.ciudad),
                "tema_lda": int(row.tema_lda),
                "url": str(row.url)
            })

    return render_template(
        'views/nlp_topicos_lda.html',
        active_page='nlp-topicos',
        topics=topics,
        sample_notes=sample_notes,
        total_notes=len(df_nlp)
    )

