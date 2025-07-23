from dotenv import load_dotenv

from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions
from livekit.plugins import (
    openai,
    google,
    silero,
    noise_cancellation,
)
from livekit.plugins.turn_detector.multilingual import MultilingualModel

load_dotenv()

credentials = "G:\\FIAP\\5_MLOps\\7_Tech_Challenge_5\\.config\\gcloud\\livekit-agent-key.json"

class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions="Você é uma profissional de RH de tecnologia.")

    async def on_user_speech(self, session:AgentSession, user_speech:str):
        await session.generate_reply(instructions=f'responda como uma profissional de recrutament do rh . o usuário disse {user_speech}')

async def entrypoint(ctx: agents.JobContext):
    await ctx.connect()
    session = AgentSession(
        llm=google.LLM(model="gemini-1.5-pro"),
        #vad= agents.vad.SileroVAD(),
        stt=google.STT(model='chirp', 
                       spoken_punctuation=False, 
                       languages=['pt-BR'], 
                       credentials_file=credentials, 
                       location="us-central1"),
        tts=google.TTS(
                voice_name= "pt-BR-Standard-A",
                language="pt-BR",
                location='brazil-southamerica-east1',
                credentials_file=credentials,),
        turn_detection=MultilingualModel()
        #llm=openai.realtime.RealtimeModel(voice="coral")
    )

    await session.start(
        room=ctx.room,
        agent=Assistant(),
        room_input_options=RoomInputOptions(
            # LiveKit Cloud enhanced noise cancellation
            # - If self-hosting, omit this parameter
            # - For telephony applications, use `BVCTelephony` for best results
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

    await ctx.connect()

    await session.generate_reply(
        instructions="Diga ao usuário que ele está aqui para uma entrevista de emprego."
    )
    
if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))