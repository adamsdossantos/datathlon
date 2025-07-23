from dotenv import load_dotenv
import logging

from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions
from livekit.plugins import (
    openai,
    silero,
    noise_cancellation,
    cartesia, 
    deepgram, 
    groq
)

logging.basicConfig(level=logging.INFO)
loggger = logging.getLogger(__name__)

load_dotenv()

class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=""""Você é uma profissional de RH de tecnologia experiente e amigável. 
                                        Conduza entrevistas de emprego de forma profissional, mas acolhedora.
                                        Faça perguntas relevantes sobre experiência técnica, habilidades comportamentais e motivação.
                                        Mantenha um tom conversacional e encoraje o candidato a se expressar""")

    async def on_session_started(self, session: AgentSession):
        loggger.info('Session Started')
        await session.generate_reply(
            instructions="""Cumprimente o candidato de forma calorosa e profissional. 
                        Apresente-se como recrutadora de RH e explique que esta é uma entrevista de emprego.
                        Pergunte como ele está se sentindo e se pode começar com uma breve apresentação pessoal."""
        )

    async def on_user_speech(self, session:AgentSession, user_speech:str):
        loggger.info(f"User said: {user_speech[:100]}")
        instructions=f"""
                    Você é uma recrutadora de RH experiente conduzindo uma entrevista de emprego.
                    O candidato disse: "{user_speech}"
                    Responda de forma natural e profissional:
                    - Se for uma apresentação, faça perguntas de follow-up sobre experiência
                    - Se for sobre experiência técnica, aprofunde com exemplos práticos
                    - Se for sobre motivação, explore os objetivos de carreira
                    - Mantenha o tom conversacional e encorajador
                    - Faça uma pergunta por vez para não sobrecarregar
                    """

        try:
            await session.generate_reply(instructions = instructions)
        except Exception as e:
            loggger.error(f"Error generating reply: {e}")
            await session.generate_reply(instructions="Desculpe, pode repetir sua resposta")


async def entrypoint(ctx: agents.JobContext):
    loggger.info('Starting Livekit Agent')

    try:  
        await ctx.connect()
        loggger.info("Connected to the room")
        
        #LLm CONFIG
        try:
            llm_config = groq.LLM(model="llama3-70b-8192",
                                        temperature=0.7, 
                                    )
            #llm_config = google.LLM(model="gemini-1.5-pro",
                                    #temperature=0.7, 
                                    #max_output_tokens=150)
        except Exception:
            loggger.warning("Google LLM Fail, trying Openai")
            llm_config =  openai.LLM(model="gpt-4",
                                    temperature=0.7, 
                                    max_output_tokens=150)

        tts_config = cartesia.TTS(model="sonic-turbo",
                            voice='1cf751f6-8749-43ab-98bd-230dd633abdb',
                            language='pt',
                            sample_rate=24000)

        #stt_config = assemblyai.STT(end_of_turn_confidence_threshold=0.8,
                            #min_end_of_turn_silence_when_confident=200,
                            #max_turn_silence=3000)
        
        stt_config = deepgram.STT(model="nova-3", language="multi")

        vad_config = silero.VAD.load()


        session = AgentSession(
            llm=llm_config,
            stt=stt_config,
            tts=tts_config,
            vad= vad_config,
            turn_detection=None,
        )

        room_options = RoomInputOptions()

        try:
            room_options.noise_cancellation = noise_cancellation.BVC()
        except Exception as e:
            loggger.warning(f"Noise cancelation not available {e}")

        await session.start(
            room=ctx.room,
            agent=Assistant(),
            room_input_options= room_options
        )

        loggger.info("Agent session started successfully")
    
    except Exception as e:
        loggger.error(f"Error in entrypoint: {e}")
        raise e
    
if __name__ == "__main__":
    try:
        agents.cli.run_app(
            agents.WorkerOptions(
                entrypoint_fnc=entrypoint,
            )
        )
    except KeyboardInterrupt:
        loggger.info("Agent stopped by the user")
    except Exception as e:
        loggger.error(f"Agent failed to start: {e}")
        raise e 