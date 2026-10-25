package tn.nightbeam.fishermanhouse.core;

/** The Crab Pot's timing and bait maths, free of Minecraft so it can be tested. */
public final class CrabPotRules {
    public static final int SLOTS = 5;
    /** The box searched for water around a pot: 5 x 3 x 5 minus the pot itself. */
    public static final int RADIUS = 2;
    public static final int MAX_WATER = 5 * 3 * 5 - 1;
    /** The shortest wait between two catches, whatever the bait and settings. */
    public static final int MIN_WAIT_TICKS = 100;

    private CrabPotRules() {
    }

    /** A bait's effect: the wait is multiplied by {@code speed}; {@code luck} is the catch's luck. */
    public enum Bait {
        NONE("", 1.0, 0),
        FISH_BAIT("fish_bait", 0.5, 0),
        CHUM("chum", 0.35, 1),
        GLOW_BAIT("glow_bait", 1.0, 3);

        private final String itemPath;
        private final double speed;
        private final int luck;

        Bait(String itemPath, double speed, int luck) {
            this.itemPath = itemPath;
            this.speed = speed;
            this.luck = luck;
        }

        public String itemPath() {
            return itemPath;
        }

        public double speed() {
            return speed;
        }

        public int luck() {
            return luck;
        }

        /** The bait for an item of this mod ({@code path} without namespace), or NONE. */
        public static Bait byItemPath(String path) {
            for (Bait bait : values()) {
                if (bait != NONE && bait.itemPath.equals(path)) {
                    return bait;
                }
            }
            return NONE;
        }
    }

    public enum Status {
        /** Not enough water around the pot (or not waterlogged): it does nothing. */
        NO_WATER,
        /** Counting down to the next catch. */
        WAITING,
        /** No slot can take the next catch; it waits instead of losing it. */
        FULL
    }

    /**
     * The wait before the next catch, in ticks.
     *
     * @param roll a random number in [0, 1)
     */
    public static int waitTicks(double roll, int minSeconds, int maxSeconds, Bait bait) {
        int min = Math.max(1, Math.min(minSeconds, maxSeconds));
        int max = Math.max(min, Math.max(minSeconds, maxSeconds));
        double seconds = min + roll * (max - min);
        return Math.max(MIN_WAIT_TICKS, (int) Math.round(seconds * 20 * bait.speed()));
    }

    /** How far the countdown advances in one tick: twice as fast in the rain when the bonus is on. */
    public static int progress(boolean rainingOnPot, boolean rainBonus) {
        return rainingOnPot && rainBonus ? 2 : 1;
    }

    public static boolean enoughWater(int waterBlocks, int minWater) {
        return waterBlocks >= Math.min(minWater, MAX_WATER);
    }

    /** Comparator output 0-15 from the number of non-empty slots and how full they are (vanilla container rule). */
    public static int comparator(double fullness, boolean anyItem) {
        if (!anyItem) {
            return 0;
        }
        return Math.min(15, 1 + (int) Math.floor(fullness * 14.0));
    }

    /** Whole seconds, rounded up, for the status line. */
    public static int seconds(int ticks) {
        return (Math.max(0, ticks) + 19) / 20;
    }
}
