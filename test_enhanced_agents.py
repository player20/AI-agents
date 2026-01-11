"""Test that enhanced agents load correctly"""
import json
from pathlib import Path

config_path = Path(__file__).parent / "agents.config.json"
config = json.load(open(config_path))

print(f"Total agents: {len(config['agents'])}")
print(f"Version: {config['version']}")

print("\nEnhanced agents sample:")
for agent in config['agents'][:8]:
    print(f"  {agent['id']:20} | {agent['role']:30} | {len(agent['backstory']):4} chars")

print("\nChecking expertise depth:")
devops = [a for a in config['agents'] if a['id'] == 'DevOps'][0]
has_expertise = "Expert in:" in devops['backstory'] and "Specializes in:" in devops['backstory']
print(f"  DevOps has detailed expertise: {has_expertise}")

print("\nAll agents loaded successfully!")
