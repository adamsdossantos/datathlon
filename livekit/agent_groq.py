import asyncio
from dotenv import load_dotenv
from livekit.agents import AgentSession, Agent, RoomInputOptions, JobContext, WorkerOptions, cli
from livekit.plugins import (
    google,
    silero,
    noise_cancellation,
    deepgram, 
    groq
)
from livekit.plugins.turn_detector.multilingual import MultilingualModel

from questions import load_interview_questions, build_system_prompt

load_dotenv()

credentials = "G:\\FIAP\\5_MLOps\\7_Tech_Challenge_5\\.config\\gcloud\\livekit-agent-key.json"

QUESTIONS_CONFIG = load_interview_questions()

SYSTEM_PROMPT = build_system_prompt(QUESTIONS_CONFIG)

llm_config = groq.LLM(model="llama3-70b-8192", temperature=0.7)
# tts_config = cartesia.TTS(model="sonic-turbo",
#                             voice='1cf751f6-8749-43ab-98bd-230dd633abdb',
#                             language='pt',
#                             sample_rate=24000)
tts_config=google.TTS(voice_name= "pt-BR-Chirp3-HD-Despina",
                language="pt-BR",
                credentials_file=credentials,
                #use_streaming=False,
                speaking_rate=1.3,
                )     
stt_config = deepgram.STT(model="nova-3", language="multi")
vad_config = silero.VAD.load()



class InterviewAgent():
    def __init__(self):
        self.config = load_interview_questions()
        self.current_section = "warm_up"
        self.current_question_index = 0
        self.questions_asked = []
        self.candidate_responses = []
        self.follow_up_count = 0
        self.max_follow_ups = self.config.get('interview_config', {}).get('settings', {}).get('max_follow_up_questions', 2)
        
        # Build question sequence from YAML config
        self.question_sequence = []
        question_sections = self.config.get('questions', {})
        
        # Add questions in order: warm_up -> cultural_fit -> engagement -> wrap_up
        for section in ['warm_up', 'cultural_fit', 'engagement', 'wrap_up']:
            if section in question_sections:
                for q in question_sections[section]:
                    self.question_sequence.append({
                        'section': section,
                        'question': q['question'],
                        'purpose': q.get('purpose', ''),
                        'follow_up_prompts': q.get('follow_up_prompts', []),
                        'key_indicators': q.get('key_indicators', [])
                    })
        
   
    def get_instructions(self) -> str:
        """Get the agent instructions from configuration"""
        return build_system_prompt(self.config)
    
    async def on_agent_speech_committed(self, message: str):
        """Track questions asked by the agent"""
        self.questions_asked.append({
            'message': message,
            'timestamp': asyncio.get_event_loop().time()
        })
        print(f"Agent asked: {message}")
    
    async def on_user_speech_committed(self, message: str):
        """Track user responses for analysis"""
        self.candidate_responses.append({
            'response': message,
            'timestamp': asyncio.get_event_loop().time()
        })
        print(f"Candidate responded: {message}")

    async def maybe_end_session(self, session: AgentSession):
        if self.current_question_index >= len(self.question_sequence):
            await session.say("Obrigado pelo seu tempo hoje. Nossa entrevista está encerrada")
            await asyncio.sleep(3)
            await session.leave()

async def entrypoint(ctx: JobContext):
    """Main entry point for the LiveKit agent using the new API"""
    
    # Create interview agent instance
    interview_agent = InterviewAgent()
    
    # Create agent with instructions from YAML config
    agent = Agent(
        instructions=interview_agent.get_instructions()
    )
    
    # Set up the agent session with voice AI pipeline
    session = AgentSession(
        # Speech-to-text
        stt=stt_config,
        # Large language model
        llm=llm_config,
        # Text-to-speech
        tts=tts_config,
        # Voice activity detection
        vad=vad_config,
        # Turn detection for natural conversation flow
        turn_detection=MultilingualModel()
    )
    
    # Add event handlers for tracking interview progress
    session.on("agent_speech_committed", lambda msg: asyncio.create_task(interview_agent.on_agent_speech_committed(msg)))
    session.on("user_speech_committed", lambda msg: asyncio.create_task(interview_agent.on_user_speech_committed(msg)))
    
    # Start the agent session
    await session.start(
        room=ctx.room,
        agent=agent,
        room_input_options=RoomInputOptions(
            # Optional: Add noise cancellation
            # noise_cancellation=noise_cancellation.BVC(),
        noise_cancellation=noise_cancellation.BVC(),
        )
    )
    
    # Get opening message from config
    opening_message = interview_agent.config.get('interview_config', {}).get('messages', {}).get(
        'opening', 
        """Olá! Obrigado pela disponibilidade de tempo para conversarmos hoje. 
        Estou aqui para aprender sobre você e discutir sobre uma oportunidade em nossa empresa. 
        Essa conversa levará entre 10 e 15 minutos. Vamos começar?
        """
    )
    
    # Send opening message
    await session.say(opening_message)



if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))