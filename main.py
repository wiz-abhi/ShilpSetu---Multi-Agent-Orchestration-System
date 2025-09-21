"""
Main application entry point for the Artisan Marketplace Multi-Agent System
"""

import asyncio
import argparse
import sys
from typing import Optional
import json

from agents.orchestrator import AgentOrchestrator
from models.data_models import ProductInput
from config.settings import Config
from utils.logger import setup_logger

class ArtisanMarketplaceApp:
    """Main application class for the multi-agent system"""
    
    def __init__(self):
        self.logger = setup_logger("ArtisanMarketplaceApp")
        self.orchestrator = AgentOrchestrator()
        
    async def process_single_product(
        self, 
        description: str,
        user_id: str,
        product_id: str,
        optional_image_url: Optional[str] = None,
        image_count: int = 2,
        output_file: Optional[str] = None
    ) -> dict:
        """Process a single product through the multi-agent system"""
        
        print(f"🎨 Processing product: {product_id}")
        print(f"📝 Description: {description}")
        if optional_image_url:
            print(f"🖼️  Reference image: {optional_image_url}")
        print(f"🔢 Generating {image_count} images")
        print("-" * 50)
        
        # Create product input
        product_input = ProductInput(
            description=description,
            optional_image_url=optional_image_url,
            user_id=user_id,
            product_id=product_id
        )
        
        # Set workflow options
        workflow_options = {
            'image_count': image_count,
            'max_retries': 3
        }
        
        try:
            # Process the product
            result = await self.orchestrator.process_product(product_input, workflow_options)
            
            # Display results
            self._display_results(result)
            
            # Save results if output file specified
            if output_file:
                self._save_results(result, output_file)
                print(f"💾 Results saved to: {output_file}")
            
            return result
            
        except Exception as e:
            print(f"❌ Error processing product: {str(e)}")
            self.logger.error(f"Product processing failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def process_batch_from_file(self, input_file: str, output_file: Optional[str] = None) -> dict:
        """Process multiple products from a JSON file"""
        
        try:
            # Load products from file
            with open(input_file, 'r') as f:
                data = json.load(f)
            
            products_data = data.get('products', [])
            batch_options = data.get('batch_options', {})
            
            print(f"📦 Processing batch of {len(products_data)} products from {input_file}")
            print("-" * 50)
            
            # Convert to ProductInput objects
            products = []
            for product_data in products_data:
                product = ProductInput(
                    description=product_data['description'],
                    optional_image_url=product_data.get('optional_image_url'),
                    user_id=product_data['user_id'],
                    product_id=product_data['product_id'],
                    additional_context=product_data.get('additional_context', {})
                )
                products.append(product)
            
            # Process batch
            result = await self.orchestrator.process_batch(products, batch_options)
            
            # Display batch results
            self._display_batch_results(result)
            
            # Save results if output file specified
            if output_file:
                self._save_results(result, output_file)
                print(f"💾 Batch results saved to: {output_file}")
            
            return result
            
        except Exception as e:
            print(f"❌ Error processing batch: {str(e)}")
            self.logger.error(f"Batch processing failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _display_results(self, result: dict):
        """Display processing results in a formatted way"""
        
        if result.get('success'):
            print("✅ Processing completed successfully!")
        elif result.get('partial_success'):
            print("⚠️  Processing partially successful")
        else:
            print("❌ Processing failed")
        
        # Execution summary
        if 'execution_summary' in result:
            summary = result['execution_summary']
            print(f"⏱️  Total execution time: {summary.get('total_execution_time', 0):.2f}s")
            print(f"✅ Agents succeeded: {summary.get('agents_succeeded', 0)}/3")
            if summary.get('agents_failed', 0) > 0:
                print(f"❌ Agents failed: {summary.get('agents_failed', 0)}/3")
        
        # Generated content
        if result.get('generated_images'):
            images = result['generated_images']
            print(f"🖼️  Generated {len(images)} images:")
            for i, img in enumerate(images, 1):
                print(f"   {i}. {img.get('image_url', 'N/A')}")
        
        if result.get('generated_video'):
            video = result['generated_video']
            print(f"🎥 Generated video: {video.get('video_url', 'N/A')}")
            if 'duration' in video:
                print(f"   Duration: {video['duration']}s")
        
        # Errors
        if result.get('errors'):
            print("⚠️  Errors encountered:")
            for error in result['errors']:
                print(f"   • {error}")
        
        print("-" * 50)
    
    def _display_batch_results(self, result: dict):
        """Display batch processing results"""
        
        print(f"📊 Batch Processing Results")
        print(f"Total products: {result.get('total_products', 0)}")
        print(f"Successful: {result.get('successful_count', 0)}")
        print(f"Failed: {result.get('failed_count', 0)}")
        print(f"Success rate: {result.get('success_rate', 0):.1f}%")
        
        if result.get('failures'):
            print("\n❌ Failed products:")
            for failure in result['failures']:
                print(f"   • {failure.get('product_id', 'Unknown')}: {failure.get('error', 'Unknown error')}")
        
        print("-" * 50)
    
    def _save_results(self, result: dict, output_file: str):
        """Save results to a JSON file"""
        try:
            with open(output_file, 'w') as f:
                json.dump(result, f, indent=2, default=str)
        except Exception as e:
            print(f"⚠️  Failed to save results: {str(e)}")
    
    async def interactive_mode(self):
        """Run the application in interactive mode"""
        
        print("🎨 Artisan Marketplace Multi-Agent System")
        print("Interactive Mode - Generate marketing content for your products")
        print("=" * 60)
        
        while True:
            try:
                print("\nOptions:")
                print("1. Process single product")
                print("2. Process batch from file")
                print("3. View system status")
                print("4. Exit")
                
                choice = input("\nSelect an option (1-4): ").strip()
                
                if choice == '1':
                    await self._interactive_single_product()
                elif choice == '2':
                    await self._interactive_batch_process()
                elif choice == '3':
                    self._display_system_status()
                elif choice == '4':
                    print("👋 Goodbye!")
                    break
                else:
                    print("❌ Invalid option. Please select 1-4.")
                    
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {str(e)}")
    
    async def _interactive_single_product(self):
        """Interactive single product processing"""
        
        print("\n📝 Enter product details:")
        
        description = input("Product description: ").strip()
        if not description:
            print("❌ Description is required")
            return
        
        user_id = input("User ID: ").strip() or "interactive_user"
        product_id = input("Product ID: ").strip() or f"product_{int(asyncio.get_event_loop().time())}"
        
        optional_image_url = input("Optional image URL (press Enter to skip): ").strip()
        if not optional_image_url:
            optional_image_url = None
        
        try:
            image_count = int(input("Number of images to generate (default 2): ").strip() or "2")
            image_count = max(1, min(image_count, Config.IMAGE_COUNT_MAX))
        except ValueError:
            image_count = 2
        
        output_file = input("Output file (press Enter to skip): ").strip()
        if not output_file:
            output_file = None
        
        await self.process_single_product(
            description=description,
            user_id=user_id,
            product_id=product_id,
            optional_image_url=optional_image_url,
            image_count=image_count,
            output_file=output_file
        )
    
    async def _interactive_batch_process(self):
        """Interactive batch processing"""
        
        input_file = input("\nEnter path to batch input file (JSON): ").strip()
        if not input_file:
            print("❌ Input file is required")
            return
        
        output_file = input("Output file (press Enter to skip): ").strip()
        if not output_file:
            output_file = None
        
        await self.process_batch_from_file(input_file, output_file)
    
    def _display_system_status(self):
        """Display current system status"""
        
        status = self.orchestrator.get_system_status()
        
        print("\n🖥️  System Status")
        print(f"Active workflows: {status['active_workflows']}")
        print(f"Max concurrent: {status['max_concurrent_workflows']}")
        print(f"Total processed: {status['total_workflows_processed']}")
        
        print("\n🤖 Agent Status:")
        for agent_type, agent_status in status['agent_status'].items():
            status_text = "🔴 Busy" if agent_status['is_busy'] else "🟢 Available"
            print(f"   {agent_type}: {status_text}")
        
        if status['recent_workflows']:
            print("\n📋 Recent Workflows:")
            for workflow in status['recent_workflows'][-5:]:  # Last 5
                print(f"   {workflow['workflow_id'][:8]}... - {workflow['status']}")

def create_sample_batch_file():
    """Create a sample batch input file"""
    
    sample_data = {
        "products": [
            {
                "description": "Handcrafted ceramic vase with intricate blue and white patterns, featuring traditional artisan techniques and glazing methods",
                "user_id": "artisan_001",
                "product_id": "ceramic_vase_001",
                "additional_context": {"category": "ceramics", "price_range": "premium", "crafting_time": "3_days"}
            },
            {
                "description": "Sustainable bamboo cutting board with natural grain patterns, eco-friendly kitchen essential made from renewable materials",
                "user_id": "artisan_002",
                "product_id": "bamboo_board_001",
                "additional_context": {"category": "kitchenware", "price_range": "mid", "material": "bamboo"}
            },
            {
                "description": "Hand-knitted wool scarf with traditional Nordic patterns, warm winter accessory made from premium merino wool",
                "user_id": "artisan_003",
                "product_id": "wool_scarf_001",
                "additional_context": {"category": "textiles", "price_range": "premium", "material": "merino_wool"}
            }
        ],
        "batch_options": {
            "max_concurrent": 2,
            "workflow_options": {
                "image_count": 2,
                "max_retries": 3,
                "use_real_apis": True
            }
        }
    }

    with open('sample_batch.json', 'w') as f:
        json.dump(sample_data, f, indent=2)
    
    print("📄 Created sample_batch.json with example products")

async def main():
    """Main application entry point"""
    
    parser = argparse.ArgumentParser(description="Artisan Marketplace Multi-Agent System")
    parser.add_argument('--mode', choices=['interactive', 'single', 'batch', 'api'], 
                       default='interactive', help='Application mode')
    parser.add_argument('--description', help='Product description (single mode)')
    parser.add_argument('--user-id', default='cli_user', help='User ID')
    parser.add_argument('--product-id', help='Product ID')
    parser.add_argument('--image-url', help='Optional image URL')
    parser.add_argument('--image-count', type=int, default=2, help='Number of images to generate')
    parser.add_argument('--input-file', help='Input file for batch processing')
    parser.add_argument('--output-file', help='Output file for results')
    parser.add_argument('--create-sample', action='store_true', help='Create sample batch file')
    parser.add_argument('--api-port', type=int, default=8000, help='API server port')
    
    args = parser.parse_args()
    
    # Create sample file if requested
    if args.create_sample:
        create_sample_batch_file()
        return
    
    # Initialize application
    app = ArtisanMarketplaceApp()
    
    try:
        if args.mode == 'interactive':
            await app.interactive_mode()
            
        elif args.mode == 'single':
            if not args.description:
                print("❌ Description is required for single mode")
                sys.exit(1)
            
            product_id = args.product_id or f"cli_product_{int(asyncio.get_event_loop().time())}"
            
            await app.process_single_product(
                description=args.description,
                user_id=args.user_id,
                product_id=product_id,
                optional_image_url=args.image_url,
                image_count=args.image_count,
                output_file=args.output_file
            )
            
        elif args.mode == 'batch':
            if not args.input_file:
                print("❌ Input file is required for batch mode")
                sys.exit(1)
            
            await app.process_batch_from_file(args.input_file, args.output_file)
            
        elif args.mode == 'api':
            print(f"🚀 Starting API server on port {args.api_port}")
            import uvicorn
            from api.workflow_api import app as api_app
            uvicorn.run(api_app, host="0.0.0.0", port=args.api_port)
            
    except KeyboardInterrupt:
        print("\n👋 Application interrupted by user")
    except Exception as e:
        print(f"❌ Application error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
