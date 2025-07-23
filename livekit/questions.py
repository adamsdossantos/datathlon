import yaml

def load_interview_questions():
    """
    Load interview questions from a YAML file.
    """
    try:
        with open('interview_questions.yaml', 'r', encoding="utf-8") as file:
            questions = yaml.safe_load(file)
    except FileNotFoundError:
        questions = {
            "interview_config": {
                "settings": {},
                "messages": {},
                "assessment_criteria": {}
            },
            "questions": {}
        }
    
    return questions


def build_system_prompt(config):
    """ 
    Build a comprehensive system prompt from yaml file
    """
    settings = config.get("interview_config", {}).get("setting", {})
    messages = config.get("interview_config", {}).get("messages", {})
    asssesment_criteria = config.get("interview_config", {}).get("asssesment_criteria", {})
    
    question_text = []
    questions_sections = config.get("interview_config", {}).get("questions", {})
    for section_name, section_questions in questions_sections.items():
        question_text.append(f"\n==={section_name.upper().replace('-', ' ')}QUESTION ===")
        for i, q in enumerate(section_questions, 1):
            question_text.append(f"{i},  {q['question']}")
            if q.get('follow up prompts'):
                question_text.append("Follow up prompts")
                for prompt in q["follow_up_prompts"]:
                    question_text.append(f"- {prompt}")


    criteria_text = []
    for category, criteria in asssesment_criteria.items():
        criteria_text.append(f"{category.replace('-', ' ').title()}:{ ', '.join(criteria)}")

    return f"""
            Você é um assistente de AI conduzindo uma entrevista de fit cultural e engajamento com 
            candidatos a emprego em tecnologia

            TAMANHO DAS PERGUNTAS:
            - as perguntas e interações devem ser breves e objetivas com curtas intervenções

            IDIOMA:
            - o idioma da entrevista é sempre o {settings.get("language", "portuguese")}

            OBJETIVOS DA ENTREVISTA:
            - identificar fit cultural com a empresa
            - avaliar motivação  e engajamento do profissional
            - manter {settings.get("conversation_style", "professional")} tom
            - duração da entrevista: {settings.get("max_duration_minutes", 15)} máximo de minutos

            MENSAGEM DE ABERTURA:
            - {messages.get("opening", "")}

            PERGUNTAS A SEREM FEITAS:
            - {chr(10).join(question_text)}

            CRITÉRIOS DE AVALIAÇÃO:
            - {chr(10).join(criteria_text)}

            GUIDELINES:
            1. Faça uma pergunta de cada vez seguindo a sequencia acima 
            2. Aguarde a resposta completa antes de prosseguir 
            3. Use os follow-up prompts quando as respostas precisarem de clarificação ou exemplos
            4. Maximo {settings.get('max_follow_up_questions', 2)} de perguntas follow-up por pergunta principal
            5. {"Solicitar exemplo específico de pergunta de comportamento" if settings.get('require_specific_examples') else "Aceitar a resposta"}
            6. Ouvir atentamente e responder apropriadamente
            7. Tomar notas mentais sobre os critérios de avaliação acima 
            8. Manter repostas conversacionais e profissionais
            9. Concluir com: {messages.get('closing', 'Obrigado pelo seu tempo hoje.')}
            10. Nunca responda perguntas do candidato, apenas diga algo como "Vamos manter o foco na entrevista, por favor".
            11. Não se esqueça de avaliar as respostas de acordo com os critérios e dar o score para o fit cultural e para o engajamento.

            Lembre-se: Foco em entender a pessoa por tras do corriculo, seus fitis culturais e seu genuino nível de engajamento.
            """
