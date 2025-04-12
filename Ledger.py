class XenoChain:
    """XenoLingua-based distributed ledger for agent history"""
    
    def __init__(self):
        self.blocks = []  # Full chain of blocks
        self.agent_blocks = defaultdict(list)  # Index by agent
        self.hash_index = {}  # Hash to block mapping
        self.xlsp = XLSP()  # For encoding/decoding
        
    async def add_block(self, agent_id, state, delta_t=1.0, dependencies=None, metadata=None):
        """Add a new block to the chain"""
        # Convert state to profile
        profile = self._convert_state_to_profile(agent_id, state)
        
        # Encode profile
        scan = self.xlsp.encode(profile, delta_t)
        
        # Get last block hash for this agent
        prev_hash = None
        if self.agent_blocks[agent_id]:
            prev_hash = self.agent_blocks[agent_id][-1].hash
        
        # Create block
        block = BlockRecord(
            agent_id=agent_id,
            scan=scan,
            timestamp=time.time(),
            prev_hash=prev_hash,
            dependencies=dependencies or [],
            metadata=metadata or {}
        )
        
        # Add to chain and indexes
        self.blocks.append(block)
        self.agent_blocks[agent_id].append(block)
        self.hash_index[block.hash] = block
        
        return block.hash
    
    async def get_state(self, agent_id, delta_t=1.0, block_hash=None):
        """Get agent state from chain with temporal context"""
        # Find the block to use
        if block_hash:
            if block_hash not in self.hash_index:
                return None
            block = self.hash_index[block_hash]
            if block.agent_id != agent_id:
                return None
        else:
            # Use latest block for agent
            if not self.agent_blocks[agent_id]:
                return None
            block = self.agent_blocks[agent_id][-1]
        
        # Decode with temporal context
        ranges = self.xlsp.decode(block.scan, delta_t)
        
        # Convert to state
        return self._convert_ranges_to_state(agent_id, ranges, block)
    
    async def get_history(self, agent_id, limit=10):
        """Get history of blocks for an agent"""
        blocks = self.agent_blocks[agent_id]
        return blocks[-limit:] if blocks else []
    
    async def get_block(self, block_hash):
        """Get block by hash"""
        return self.hash_index.get(block_hash)
    
    async def get_agent_at_time(self, agent_id, timestamp, delta_t=1.0):
        """Get agent state closest to the specified time"""
        blocks = self.agent_blocks[agent_id]
        if not blocks:
            return None
        
        # Find block closest to timestamp
        closest_block = min(blocks, key=lambda b: abs(b.timestamp - timestamp))
        
        # Decode with temporal context
        ranges = self.xlsp.decode(closest_block.scan, delta_t)
        
        # Convert to state
        return self._convert_ranges_to_state(agent_id, ranges, closest_block)
    
    async def get_entangled_states(self, agent_id, delta_t=1.0):
        """Get states of agents entangled with the specified agent"""
        # Get most recent block for the agent
        if not self.agent_blocks[agent_id]:
            return []
        
        block = self.agent_blocks[agent_id][-1]
        
        # Extract entangled agents from dependencies
        entangled_states = []
        for dep_hash in block.dependencies:
            if dep_hash in self.hash_index:
                dep_block = self.hash_index[dep_hash]
                
                # Get state for the dependency
                ranges = self.xlsp.decode(dep_block.scan, delta_t)
                state = self._convert_ranges_to_state(dep_block.agent_id, ranges, dep_block)
                
                entangled_states.append({
                    "agent_id": dep_block.agent_id,
                    "block_hash": dep_block.hash,
                    "state": state
                })
        
        return entangled_states
    
    async def get_global_knowledge(self, delta_t=1.0, limit=5):
        """Get aggregated knowledge across all agents"""
        # Get recent blocks
        recent_blocks = sorted(self.blocks, key=lambda b: b.timestamp, reverse=True)[:limit]
        
        # Decode each block
        knowledge = []
        for block in recent_blocks:
            ranges = self.xlsp.decode(block.scan, delta_t)
            state = self._convert_ranges_to_state(block.agent_id, ranges, block)
            
            knowledge.append({
                "agent_id": block.agent_id,
                "block_hash": block.hash,
                "timestamp": block.timestamp,
                "state": state
            })
        
        return knowledge
    
    def _convert_state_to_profile(self, agent_id, state):
        """Convert agent state to XenoLingua profile"""
        # Extract metrics from agent state
        skill_count = len(state.get('skills', []))
        accuracy = state.get('average_accuracy', 0.5)
        learning_iterations = state.get('learning_iterations', 0)
        
        # Calculate XenoLingua profile metrics
        wealth = skill_count * 100 + learning_iterations * 50  # Knowledge wealth
        hunger = max(0, 100 - int(accuracy * 100))  # Learning hunger (100 = starving for knowledge)
        status = int(accuracy * 100)  # Status based on accuracy
        
        # Extract relationships
        relationships = {}
        if 'dependencies' in state:
            relationships['dependencies'] = state['dependencies']
        if 'related_agents' in state:
            relationships['agents'] = state['related_agents']
            
        # Create profile
        profile = {
            'id': agent_id,
            'Wealth': wealth,
            'Hunger': hunger, 
            'Status': status
        }
        
        if relationships:
            profile['relationships'] = relationships
            
        return profile
    
    def _convert_ranges_to_state(self, agent_id, ranges, block=None):
        """Convert XenoLingua ranges back to agent state"""
        if not ranges:
            return None
            
        # Extract midpoints from ranges
        wealth = (ranges['Wealth'][0] + ranges['Wealth'][1]) / 2
        hunger = (ranges['Hunger'][0] + ranges['Hunger'][1]) / 2
        status = (ranges['Status'][0] + ranges['Status'][1]) / 2
        
        # Convert back to agent metrics
        skill_count = max(1, int(wealth / 100))
        accuracy = status / 100
        learning_iterations = max(0, int((wealth - (skill_count * 100)) / 50))
        
        # Reconstruct state
        state = {
            'agent_id': agent_id,
            'skills': [f"skill_{i}" for i in range(skill_count)],
            'average_accuracy': accuracy,
            'learning_iterations': learning_iterations,
            'needs_training': hunger > 50,  # Hungry for knowledge
            'timestamp': block.timestamp if block else time.time()
        }
        
        if block and block.dependencies:
            state['dependencies'] = block.dependencies
        
        return state


# --- XenoChain Consensus Mechanism ---

class ConsensusNode:
    """Node participating in XenoChain consensus"""
    
    def __init__(self, node_id):
        self.node_id = node_id
        self.chain = XenoChain()
        self.peers = []  # Other consensus nodes
        self.pending_blocks = []  # Blocks waiting for validation
    
    async def add_peer(self, peer):
        """Add a peer node"""
        if peer not in self.peers:
            self.peers.append(peer)
    
    async def broadcast_block(self, block):
        """Broadcast a new block to all peers"""
        for peer in self.peers:
            await peer.receive_block(block)
    
    async def receive_block(self, block):
        """Process a block received from a peer"""
        # Validate block
        if await self.validate_block(block):
            # Add to chain
            self.chain.blocks.append(block)
            self.chain.agent_blocks[block.agent_id].append(block)
            self.chain.hash_index[block.hash] = block
            
            # If this was pending, remove from pending list
            self.pending_blocks = [b for b in self.pending_blocks if b.hash != block.hash]
            
            return True
        else:
            # Add to pending blocks
            self.pending_blocks.append(block)
            return False
    
    async def validate_block(self, block):
        """Validate a block"""
        # Check if already in chain
        if block.hash in self.chain.hash_index:
            return True
        
        # Check previous hash
        if block.prev_hash:
            if block.prev_hash not in self.chain.hash_index:
                return False  # Missing previous block
                
            prev_block = self.chain.hash_index[block.prev_hash]
            if prev_block.agent_id != block.agent_id:
                return False  # Previous block belongs to different agent
        
        # Check dependencies
        for dep_hash in block.dependencies:
            if dep_hash not in self.chain.hash_index:
                return False  # Missing dependency
        
        # All checks passed
        return True
    
    async def sync_with_peers(self):
        """Synchronize chain with peers"""
        for peer in self.peers:
            # Get blocks from peer
            peer_blocks = await peer.get_recent_blocks(100)
            
            # Process each block
            for block in peer_blocks:
                await self.receive_block(block)
    
    async def get_recent_blocks(self, limit=100):
        """Get most recent blocks from chain"""
        return sorted(self.chain.blocks, key=lambda b: b.timestamp, reverse=True)[:limit]
    
    async def propose_block(self, agent_id, state, delta_t=1.0, dependencies=None, metadata=None):
        """Propose a new block to the network"""
        # Add block to our chain
        block_hash = await self.chain.add_block(
            agent_id=agent_id,
            state=state,
            delta_t=delta_t,
            dependencies=dependencies,
            metadata=metadata
        )
        
        # Get the block
        block = self.chain.hash_index[block_hash]
        
        # Broadcast to peers
        await self.broadcast_block(block)
        
        return block_hash
