from agents.topic_agent import TopicAgent
from agents.script_agent import ScriptAgent
import json

def test():
    print("Testing Topic Agent...")
    topic_agent = TopicAgent()
    topic = topic_agent.get_trending_topic()
    print(f"Topic: {topic}")
    
    if topic:
        print("\nTesting Script Agent...")
        script_agent = ScriptAgent()
        script = script_agent.generate_script(topic)
        print(json.dumps(script, indent=2))

if __name__ == "__main__":
    test()
