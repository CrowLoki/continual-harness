#!/usr/bin/env python3
"""
Continual Harness — Hermes Integration Script
Spawns a CH episode with MCP server access.

Usage:
    python3 ch_spawn.py --game emerald --scaffold continualharness
    python3 ch_spawn.py --game red --scaffold pokeagent --agent hermes
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

CH_HOME = Path.home() / ".hermes/github/CrowLoki/continual-harness"
CH_VENV = CH_HOME / ".venv/bin/python"
MCP_SERVERS = {
    "hermes_memory": {
        "command": str(Path.home() / ".hermes/hermes-agent/venv/bin/python"),
        "args": [str(Path.home() / ".hermes/github/CrowLoki/Hermes/tools/hermes-memory/server.py")]
    },
    "conversation_memory": {
        "command": str(Path.home() / ".crowclaw/venv/bin/python"),
        "args": [str(Path.home() / ".hermes/github/CrowLoki/conversation-memory/server.py")],
        "env": {
            "EMBED_MODEL": "nomic-embed-text-v2-moe",
            "MEMORY_DB_PATH": str(Path.home() / ".conversation-memory/memory.sqlite")
        }
    },
    "crowclaw_memory": {
        "command": str(Path.home() / ".crowclaw/venv/bin/python"),
        "args": [str(Path.home() / ".hermes/github/CrowLoki/crowclaw-memory/server.py")],
        "env": {
            "EMBED_MODEL": "nomic-embed-text-v2-moe",
            "MEMORY_DB_PATH": str(Path.home() / ".crowclaw/memory/crowclaw_memory.sqlite")
        }
    }
}


def check_dependencies():
    """Check that CH dependencies are available."""
    result = subprocess.run(
        [str(CH_VENV), "-c", "import flask; import fastapi; print('ok')"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print("ERROR: CH dependencies not available. Run: cd continual-harness && uv sync")
        return False
    return True


def check_roms():
    """Check if game ROMs are available."""
    rom_dir = CH_HOME / "run_data"
    if not rom_dir.exists():
        print(f"WARNING: ROM directory not found at {rom_dir}")
        print("Continual Harness needs game ROMs to run.")
        return False
    
    roms = list(rom_dir.glob("*.gba"))
    if not roms:
        print(f"WARNING: No .gba ROMs found in {rom_dir}")
        return False
    
    print(f"Found ROMs: {[r.name for r in roms]}")
    return True


def spawn_episode(game="emerald", scaffold="continualharness", agent="hermes", 
                  enable_optimization=True, max_steps=1000):
    """Spawn a Continual Harness episode."""
    
    if not check_dependencies():
        return False
    
    check_roms()  # Warn but don't fail
    
    cmd = [
        str(CH_VENV),
        str(CH_HOME / "run.py"),
        f"--game", game,
        f"--scaffold", scaffold,
        f"--agent", agent,
        f"--max-steps", str(max_steps),
    ]
    
    if enable_optimization:
        cmd.append("--enable-prompt-optimization")
    
    # Set environment for MCP access
    env = os.environ.copy()
    env["CH_MCP_SERVERS"] = json.dumps(MCP_SERVERS)
    env["CH_GAME"] = game
    env["CH_SCAFFOLD"] = scaffold
    
    print(f"Spawning CH episode: game={game}, scaffold={scaffold}, agent={agent}")
    print(f"Command: {' '.join(cmd)}")
    print()
    
    result = subprocess.run(cmd, env=env, cwd=str(CH_HOME))
    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser(description="Continual Harness — Hermes Integration")
    parser.add_argument("--game", default="emerald", choices=["emerald", "red"], help="Game to play")
    parser.add_argument("--scaffold", default="continualharness", 
                        choices=["continualharness", "pokeagent", "simple", "simplest"],
                        help="Scaffold type")
    parser.add_argument("--agent", default="hermes", help="Agent name")
    parser.add_argument("--max-steps", type=int, default=1000, help="Maximum steps")
    parser.add_argument("--no-optimize", action="store_true", help="Disable prompt optimization")
    parser.add_argument("--check", action="store_true", help="Only check dependencies")
    
    args = parser.parse_args()
    
    if args.check:
        ok = check_dependencies()
        check_roms()
        sys.exit(0 if ok else 1)
    
    ok = spawn_episode(
        game=args.game,
        scaffold=args.scaffold,
        agent=args.agent,
        enable_optimization=not args.no_optimize,
        max_steps=args.max_steps
    )
    
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
