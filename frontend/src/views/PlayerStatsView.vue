<template>
    <div>
        <!-- TODO Chris: 13/04/2025 - Refactor this -->
        <div class="mb-4">
            <router-link to="/" class="text-poker-blue hover:underline flex items-center">
                <span class="mr-1">←</span> Back to Dashboard
            </router-link>
        </div>

        <div v-if="loading" class="text-center py-8">
            <p class="text-xl">Loading player statistics...</p>
        </div>

        <div v-else-if="error" class="text-center py-8">
            <p class="text-xl text-red-500">{{ error }}</p>
            <button @click="fetchPlayerStats" class="btn-primary mt-4">Try Again</button>
        </div>

        <div v-else>
            <h1 class="text-3xl font-bold mb-6">{{ stats.player_name }}</h1>

            <!-- Key Stats Overview -->
            <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
                <div class="stat-card">
                    <span class="stat-label">Hands Played</span>
                    <span class="stat-value">{{ stats.hands_played }}</span>
                </div>

                <div class="stat-card">
                    <span class="stat-label">Win Rate</span>
                    <span class="stat-value">{{ stats.win_rate.toFixed(1) }}%</span>
                </div>

                <div class="stat-card">
                    <span class="stat-label">Total Winnings</span>
                    <span class="stat-value" :class="stats.total_winnings >= 0 ? 'text-green-600' : 'text-red-600'">
                        ${{ stats.total_winnings.toFixed(2) }}
                     </span>
                </div>

                <div class="stat-card">
                    <span class="stat-label">Average Stack</span>
                    <span class="stat-value">${{ stats.avg_stack.toFixed(2) }}</span>
                </div>
            </div>

            <!-- Detailed Stats -->
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                    <div class="bg-white rounded-lg shadow-md p-6">
                        <h2 class="text-xl font-semibold mb-4">Playing Style</h2>

                        <div class="space-y-4">
                            <div>
                                <div class="flex justify-between mb-1">
                                    <span class="text-sm font-medium">VPIP (Voluntarily Put $ In Pot)</span>
                                    <span class="text-sm font-medium">{{ stats.vpip.toFixed(1) }}%</span>
                                </div>
                                <div class="w-full bg-gray-200 rounded-full h-2">
                                    <div class="bg-poker-blue h-2 rounded-full"
                                         :style="{ width: `${Math.min(stats.vpip, 100)}%` }"></div>
                                </div>
                                <p class="text-xs text-gray-500 mt-1">
                                    Percentage of hands where player voluntarily put money in the pot preflop
                                </p>
                            </div>

                            <div>
                                <div class="flex justify-between mb-1">
                                    <span class="text-sm font-medium">PFR (Pre-Flop Raise)</span>
                                    <span class="text-sm font-medium">{{ stats.pfr.toFixed(1) }}%</span>
                                </div>
                                <div class="w-full bg-gray-200 rounded-full h-2">
                                    <div class="bg-poker-blue h-2 rounded-full"
                                         :style="{ width: `${Math.min(stats.pfr, 100)}%` }"></div>
                                </div>
                                <p class="text-xs text-gray-500 mt-1">
                                    Percentage of hands where player raised preflop
                                </p>
                            </div>

                            <div>
                                <div class="flex justify-between mb-1">
                                    <span class="text-sm font-medium">AF (Aggression Factor)</span>
                                    <span class="text-sm font-medium">{{ stats.af.toFixed(2) }}</span>
                                </div>
                                <div class="w-full bg-gray-200 rounded-full h-2">
                                    <div class="bg-poker-blue h-2 rounded-full"
                                         :style="{ width: `${Math.min(stats.af * 10, 100)}%` }"></div>
                                </div>
                                <p class="text-xs text-gray-500 mt-1">
                                    Ratio of aggressive actions (bets/raises) to passive actions (calls)
                                </p>
                            </div>
                        </div>
                    </div>

                    <div class="bg-white rounded-lg shadow-md p-6">
                        <h2 class="text-xl font-semibold mb-4">Performance Summary</h2>

                        <div class="flex items-center justify-between mb-4">
                            <div>
                                <p class="text-sm font-medium">Win/Loss Ratio</p>
                                <p class="text-2xl font-bold">
                                    {{ stats.hands_won }} / {{ stats.hands_played - stats.hands_won }}
                                </p>
                            </div>

                            <div class="h-24 w-24">
                                <!-- Simple pie chart representation -->
                                <div class="relative h-full w-full rounded-full overflow-hidden">
                                    <div class="absolute inset-0 bg-red-500"></div>
                                    <div
                                        class="absolute inset-0 bg-green-500 origin-center"
                                        :style="{
                        transform: `rotate(${360 * (stats.hands_played - stats.hands_won) / stats.hands_played}deg)`,
                        clipPath: 'polygon(50% 0, 100% 0, 100% 100%, 50% 100%, 50% 50%)'
                      }"
                                    ></div>
                                    <div
                                        class="absolute inset-0 bg-green-500 origin-center"
                                        :style="{
                        transform: `rotate(${180 + 360 * (stats.hands_played - stats.hands_won) / stats.hands_played}deg)`,
                        clipPath: 'polygon(50% 0, 100% 0, 100% 100%, 50% 100%, 50% 50%)'
                      }"
                                        v-if="stats.hands_won / stats.hands_played > 0.5"
                                    ></div>
                                    <div class="absolute inset-0 flex items-center justify-center">
                                        <div class="bg-white rounded-full h-16 w-16 flex items-center justify-center">
                        <span class="text-sm font-bold">
                          {{ (stats.win_rate).toFixed(0) }}%
                        </span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="mt-6">
                            <h3 class="text-sm font-medium mb-2">Player Type</h3>
                            <div class="flex items-center space-x-2">
                  <span
                      class="px-3 py-1 rounded-full text-xs font-medium"
                      :class="getPlayerTypeClass()"
                  >
                    {{ getPlayerType() }}
                  </span>
                            </div>
                        </div>
                    </div>
                </div>

            <!-- Recent Results -->
            <div class="bg-white rounded-lg shadow-md p-6">
                <h2 class="text-xl font-semibold mb-4">Recent Results</h2>

                <div class="overflow-x-auto">
                    <table class="min-w-full divide-y divide-gray-200">
                        <thead>
                        <tr>
                            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Hand
                            </th>
                            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Date
                            </th>
                            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Result
                            </th>
                            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Profit/Loss
                            </th>
                            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Pot Size
                            </th>
                        </tr>
                        </thead>
                        <tbody class="divide-y divide-gray-200">
                        <tr v-for="result in stats.recent_results" :key="result.hand_id">
                            <td class="px-4 py-3 text-sm">{{ result.hand_id }}</td>
                            <td class="px-4 py-3 text-sm">{{ formatDate(result.date_time) }}</td>
                            <td class="px-4 py-3">
                            <span class="px-2 py-1 text-xs rounded-full"
                                :class="result.won ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'"
                            >
                                {{ result.won ? 'Won' : 'Lost' }}
                            </span>
                            </td>
                            <td class="px-4 py-3 text-sm font-medium"
                                :class="result.profit >= 0 ? 'text-green-600' : 'text-red-600'">
                                ${{ result.profit.toFixed(2) }}
                            </td>
                            <td class="px-4 py-3 text-sm">${{ result.pot.toFixed(2) }}</td>
                        </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import api from '@/services/api';

export default {
    name: 'PlayerStatsView',
    props: {
        playerName: {
            type: String,
            required: true
        }
    },
    data() {
        return {
            stats: null,
            loading: true,
            error: null
        };
    },
    created() {
        this.fetchPlayerStats();
    },
    methods: {
        async fetchPlayerStats() {
            try {
                this.loading = true;
                this.error = null;
                const response = await api.getPlayerStats(this.playerName);
                this.stats = response.data;
            } catch(error) {
                console.error('Error fetching player stats:', error);
                this.error = error.response?.data?.detail || 'Failed to load player statistics. Please try again.';
            } finally {
                this.loading = false;
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
        },
        getPlayerType() {
            const {vpip, pfr, af} = this.stats;

            if(vpip < 15) {
                return 'Rock (Tight-Passive)';
            } else if(vpip < 25 && pfr > 15 && af > 2) {
                return 'TAG (Tight-Aggressive)';
            } else if(vpip > 30 && pfr > 20 && af > 2.5) {
                return 'LAG (Loose-Aggressive)';
            } else if(vpip > 30 && pfr < 15) {
                return 'Calling Station (Loose-Passive)';
            } else {
                return 'Balanced';
            }
        },
        getPlayerTypeClass() {
            const playerType = this.getPlayerType();

            const classMap = {
                'Rock (Tight-Passive)': 'bg-gray-200 text-gray-800',
                'TAG (Tight-Aggressive)': 'bg-blue-100 text-blue-800',
                'LAG (Loose-Aggressive)': 'bg-red-100 text-red-800',
                'Calling Station (Loose-Passive)': 'bg-yellow-100 text-yellow-800',
                'Balanced': 'bg-green-100 text-green-800'
            };

            return classMap[playerType] || 'bg-gray-100 text-gray-800';
        }
    }
};
</script>
