import asyncio
import os
import sys

# Ensure backend can be imported
sys.path.append(os.getcwd())

from backend.app.conversation.checkpoint_manager import CheckpointManager

async def test():
    db_path = "test_checkpoint.db"
    if os.path.exists(db_path):
        os.remove(db_path)
    
    manager = CheckpointManager(db_path)
    conv_id = "test_conv_1"
    
    # Test 1: Add user message to new conversation
    print("Test 1: Adding first user message...")
    await manager.add_message(conv_id, "user", "Hello world this is a test message")
    
    # Check title
    convs = await manager.list_conversations()
    assert len(convs) == 1
    print(f"Title after 1st message: {convs[0]['title']}")
    assert convs[0]['title'] == "Hello world this is a test message"
    
    # Test 2: Add second user message
    print("Test 2: Adding second user message...")
    await manager.add_message(conv_id, "user", "Second message")
    
    # Check title should not change
    convs = await manager.list_conversations()
    print(f"Title after 2nd message: {convs[0]['title']}")
    assert convs[0]['title'] == "Hello world this is a test message"
    
    # Test 3: Long message
    conv_id_2 = "test_conv_2"
    long_msg = "This is a very long message " * 10
    print("Test 3: Adding long user message...")
    await manager.add_message(conv_id_2, "user", long_msg)
    
    convs = await manager.list_conversations()
    # Find conv 2
    conv2 = next(c for c in convs if c['id'] == conv_id_2)
    print(f"Title for long message: {conv2['title']}")
    assert len(conv2['title']) <= 53 # 50 + ...
    assert conv2['title'].endswith("...")
    
    # Test 4: System message first
    conv_id_3 = "test_conv_3"
    print("Test 4: Adding system message first...")
    await manager.add_message(conv_id_3, "system", "System prompt")
    
    convs = await manager.list_conversations()
    conv3 = next(c for c in convs if c['id'] == conv_id_3)
    print(f"Title after system message: {conv3['title']}")
    assert conv3['title'] == "新对话"
    
    # Add user message
    print("Test 4b: Adding user message after system...")
    await manager.add_message(conv_id_3, "user", "User follows up")
    
    convs = await manager.list_conversations()
    conv3 = next(c for c in convs if c['id'] == conv_id_3)
    print(f"Title after user message: {conv3['title']}")
    assert conv3['title'] == "User follows up"

    # Clean up
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except:
            pass
    print("All tests passed!")

if __name__ == "__main__":
    asyncio.run(test())
