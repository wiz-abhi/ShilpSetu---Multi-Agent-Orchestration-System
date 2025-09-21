"""
Script to run the orchestrator with sample data
"""

import asyncio
from models.data_models import ProductInput
from agents.orchestrator import AgentOrchestrator

async def main():
    """Run the orchestrator with sample product data"""
    print("🚀 Starting Artisan Marketplace Multi-Agent System Demo")
    
    # Initialize orchestrator
    orchestrator = AgentOrchestrator()
    
    sample_products = [
        ProductInput(
            description="Handcrafted ceramic vase with intricate blue and white patterns, perfect for home decoration. Features traditional glazing techniques and unique artistic design.",
            user_id="artisan_001",
            product_id="ceramic_vase_001",
            additional_context={"category": "ceramics", "price_range": "premium", "crafting_time": "3_days"}
        ),
        ProductInput(
            description="Wooden cutting board made from sustainable bamboo with natural grain patterns. Eco-friendly kitchen essential with antimicrobial properties.",
            user_id="artisan_002", 
            product_id="bamboo_board_001",
            additional_context={"category": "kitchenware", "price_range": "mid", "material": "bamboo"}
        )
    ]
    
    print(f"Processing {len(sample_products)} sample products...")
    
    # Process single product
    print("\n--- Processing Single Product ---")
    result = await orchestrator.process_product(sample_products[0])
    
    print(f"✓ Workflow completed: {result['success']}")
    if result.get('partial_success'):
        print("⚠ Partial success - some agents failed")
    
    print(f"Execution time: {result.get('execution_summary', {}).get('total_execution_time', 0):.2f}s")
    
    if result.get('generated_images'):
        print(f"Generated {len(result['generated_images'])} images")
    
    if result.get('generated_video'):
        print("Generated marketing video")
    
    if result.get('errors'):
        print(f"Errors encountered: {result['errors']}")
    
    # Process batch
    print("\n--- Processing Batch ---")
    batch_result = await orchestrator.process_batch(sample_products)
    
    print(f"✓ Batch completed: {batch_result['successful_count']}/{batch_result['total_products']} successful")
    print(f"Success rate: {batch_result['success_rate']:.1f}%")
    
    # Show system status
    print("\n--- System Status ---")
    status = orchestrator.get_system_status()
    print(f"Active workflows: {status['active_workflows']}")
    print(f"Total processed: {status['total_workflows_processed']}")
    
    for agent_type, agent_status in status['agent_status'].items():
        print(f"{agent_type}: {'Busy' if agent_status['is_busy'] else 'Available'}")
    
    print("\n🎉 Demo completed successfully!")

if __name__ == "__main__":
    asyncio.run(main())
