"""Test plugin manager with template filtering"""
import asyncio
from windows_ai.core.plugin_manager import get_plugin_manager

async def test_plugin_loading():
    """Test that only working plugins load (not templates)"""
    print("Testing plugin manager with template filtering...")
    print("=" * 60)
    
    # Get plugin manager instance
    pm = get_plugin_manager()
    
    # Initialize (this should skip templates under 5KB)
    print("\nInitializing plugin manager...")
    result = await pm.initialize()
    print(f"Initialization result: {result}")
    
    # Get statistics
    stats = pm.get_stats()
    print(f"\n{'PLUGIN STATISTICS':^60}")
    print("=" * 60)
    print(f"Total plugins loaded: {stats['total_plugins']}")
    print(f"\nExpected: ~132 working plugins (NOT 2,640 total)")
    print(f"Status: {'✅ PASS' if 100 <= stats['total_plugins'] <= 150 else '❌ FAIL'}")
    
    print(f"\nPlugin Types:")
    for ptype, count in stats['plugin_types'].items():
        print(f"  {ptype}: {count}")
    
    print(f"\nTop Categories (showing first 10):")
    sorted_cats = sorted(stats['categories'].items(), key=lambda x: x[1], reverse=True)
    for i, (cat, count) in enumerate(sorted_cats[:10]):
        print(f"  {cat}: {count}")
    
    # List all loaded plugins
    print(f"\n{'LOADED PLUGINS':^60}")
    print("=" * 60)
    all_plugins = pm.get_all_plugins()
    
    # Show first 20 plugins
    print(f"Showing first 20 of {len(all_plugins)} plugins:")
    for plugin_info in all_plugins[:20]:
        print(f"  • {plugin_info['id']:<40} ({plugin_info['plugin_type']})")
    
    if len(all_plugins) > 20:
        print(f"  ... and {len(all_plugins) - 20} more plugins")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    
    # Cleanup
    await pm.shutdown()

if __name__ == "__main__":
    asyncio.run(test_plugin_loading())
