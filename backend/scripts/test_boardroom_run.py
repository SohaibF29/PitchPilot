import asyncio
import os
import sys
from uuid import UUID

from dotenv import load_dotenv
load_dotenv()

# Add backend dir to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.infrastructure.database.connection import AsyncSessionLocal
from app.infrastructure.repositories.meeting_repository import MeetingRepository
from app.infrastructure.repositories.api_key_repository import ApiKeyRepository
from app.application.services.api_key_service import ApiKeyService
from app.application.services.meeting_service import MeetingService
from app.agents.checkpointer import PostgresCheckpointerManager
from app.config import get_settings

settings = get_settings()
ANONYMOUS_USER_ID = UUID(int=0)

async def main():
    print("Initializing test run...")
    
    # 1. Setup Checkpointer
    checkpointer_manager = PostgresCheckpointerManager(settings.database_url_psycopg)
    checkpointer = await checkpointer_manager.initialize()
    
    async with AsyncSessionLocal() as session:
        # 2. Setup Repos and Services
        meeting_repo = MeetingRepository(session)
        api_key_repo = ApiKeyRepository(session)
        api_key_service = ApiKeyService(api_key_repo)
        meeting_service = MeetingService(
            meeting_repo=meeting_repo,
            checkpointer=checkpointer,
            search_service=None,
            api_key_service=api_key_service
        )
        
        # 3. Ensure API keys exist in DB for ANONYMOUS_USER_ID
        openai_key = os.getenv("OPENAI_API_KEY")
        tavily_key = os.getenv("TAVILY_API_KEY")
        
        print(f"Setting up API keys for user {ANONYMOUS_USER_ID}")
        if openai_key:
            await api_key_service.save_persistent_key(ANONYMOUS_USER_ID, "openai", openai_key)
        if tavily_key:
            await api_key_service.save_persistent_key(ANONYMOUS_USER_ID, "tavily", tavily_key)
            
        await session.commit()
        
        # 4. Create Meeting
        title = "EcoDrive Innovations"
        pitch_text = "EcoDrive Innovations is building a retrofittable electric motor module for commercial delivery trucks. We allow fleet operators to convert existing diesel trucks to hybrid-electric vehicles for 10% of the cost of a new EV truck, extending the vehicle lifespan and reducing emissions by 40%. We have completed prototype testing with a local logistics company and are seeking seed funding to start manufacturing our first 100 units."
        print(f"Creating meeting: {title}")
        meeting = await meeting_service.create_meeting(ANONYMOUS_USER_ID, title, pitch_text)
        await session.commit()
        print(f"Meeting created with ID: {meeting.id}")
        
        # 5. Execute Boardroom
        print("Starting boardroom execution. This will take a minute or two as agents deliberate...")
        completed_meeting = await meeting_service.execute_boardroom(meeting.id)
        
        # 6. Print Results
        print("\n" + "="*50)
        print("BOARDROOM EXECUTION COMPLETED")
        print("="*50)
        print(f"Status: {completed_meeting.status}")
        print(f"Total Tokens: {completed_meeting.metrics.total_tokens}")
        print(f"Total Latency: {completed_meeting.metrics.total_latency_ms} ms")
        print(f"Estimated Cost: ${completed_meeting.metrics.estimated_cost}")
        
        print("\nAgent Outputs:")
        if not completed_meeting.agent_outputs:
            print("No agent outputs found. Did it fail?")
        else:
            for agent_name, output in completed_meeting.agent_outputs.items():
                print(f"\n--- {agent_name.upper()} ---")
                print(f"Tokens: {output.tokens_used}, Latency: {output.latency_ms} ms")
                print(output.content[:200] + "..." if len(output.content) > 200 else output.content)
            
    await checkpointer_manager.close()

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
