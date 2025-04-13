<template>
    <div>
        <h1 class="text-2xl font-bold mb-6">Poker Stats Dashboard</h1>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div class="md:col-span-1">
                <div class="bg-white rounded-lg shadow-md p-4">
                    <h2 class="text-xl font-semibold mb-4">Players</h2>
                    <div v-if="loading.players" class="text-center py-4">
                        <p>Loading players...</p>
                    </div>
                    <div v-else-if="error.players" class="text-center py-4 text-red-500">
                        <p>{{ error.players }}</p>
                    </div>
                    <ul v-else class="divide-y">
                        <li v-for="player in players" :key="player" class="py-2">
                            <router-link
                                :to="{ name: 'player-stats', params: { playerName: player } }"
                                class="block hover:bg-gray-100 p-2 rounded transition-colors"
                            >
                                {{ player }}
                            </router-link>
                        </li>
                    </ul>
                </div>
            </div>

            <!-- todo - refactor this - too nested! -->
            <div class="md:col-span-2">
                <div class="bg-white rounded-lg shadow-md p-4">
                    <h2 class="text-xl font-semibold mb-4">Recent Hands</h2>
                    <div v-if="loading.hands" class="text-center py-4">
                        <p>Loading recent hands...</p>
                    </div>
                    <div v-else-if="error.hands" class="text-center py-4 text-red-500">
                        <p>{{ error.hands }}</p>
                    </div>
                    <div v-else-if="recentHands.length === 0" class="text-center py-4">
                        <p>No recent hands found.</p>
                    </div>
                    <div v-else>
                        <div v-for="hand in recentHands" :key="hand.hand_id"
                             class="mb-4 p-3 border border-gray-200 rounded-lg">
                            <div class="flex justify-between items-start">
                                <div>
                                    <h3 class="font-medium">Hand #{{ hand.hand_id }}</h3>
                                    <p class="text-sm text-gray-500">{{ formatDate(hand.date_time) }}</p>
                                </div>
                                <div class="text-right">
                                    <p class="font-semibold">Pot: ${{ hand.pot.toFixed(2) }}</p>
                                </div>
                            </div>
                            <div class="mt-2">
                                <p class="text-sm">
                                    <span class="font-medium">Players:</span>
                                    {{ hand.players.join(', ') }}
                                </p>
                                <p class="text-sm mt-1">
                                    <span class="font-medium">Winners:</span>
                                    <span v-for="(winner, index) in hand.winners" :key="index" class="ml-1">
                                        {{ winner.player }} (${{ winner.amount.toFixed(2) }})
                                        {{ index < hand.winners.length - 1 ? ',' : '' }}
                                    </span>
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import api from '@/services/api';

export default {
    name: 'HomeView',
    data() {
        return {
            players: [],
            recentHands: [],
            loading: {
                players: true,
                hands: true
            },
            error: {
                players: null,
                hands: null
            }
        };
    },
    created() {
        this.fetchPlayers();
        this.fetchRecentHands();
    },
    methods: {
        async fetchPlayers() {
            try {
                this.loading.players = true;
                const response = await api.getPlayers();
                this.players = response.data.players;
            } catch(error) {
                console.error('Error fetching players:', error);
                this.error.players = 'Failed to load players. Please try again.';
            } finally {
                this.loading.players = false;
            }
        },
        async fetchRecentHands() {
            try {
                this.loading.hands = true;
                const response = await api.getRecentHands();
                this.recentHands = response.data.hands;
            } catch(error) {
                console.error('Error fetching recent hands:', error);
                this.error.hands = 'Failed to load recent hands. Please try again.';
            } finally {
                this.loading.hands = false;
            }
        },
        formatDate(dateString) {
            const date = new Date(dateString);
            return new Intl.DateTimeFormat('en-US', {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            }).format(date);
        }
    }
};
</script>
