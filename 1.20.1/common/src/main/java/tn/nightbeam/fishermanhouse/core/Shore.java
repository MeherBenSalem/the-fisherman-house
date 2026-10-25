package tn.nightbeam.fishermanhouse.core;

import java.util.List;
import java.util.Locale;
import java.util.OptionalInt;

/**
 * Decides whether a coastal structure fits a spot, and at which height, from columns sampled before features are
 * placed. Each column gives the first free block above the surface with water ({@code surface}) and without it
 * ({@code ground}); their difference is the water depth there.
 *
 * <p>A structure lists "dry" sample points (its land part, which must be dry ground) and "wet" sample points (where its
 * dock, pier or hull must find water). The caller turns the points for each rotation and asks {@link #baseY}.
 */
public final class Shore {
    private Shore() {
    }

    public enum Mode {
        /** Land part on dry ground (its average height), wet points over water. Cottages, piers, boathouses. */
        LAND,
        /** Every point over water; placed on the water's surface. The ice camp (the sea freezes under it). */
        WATER,
        /** Every point over deep water; placed on the lowest point of the sea floor. The wreck. */
        SEAFLOOR,
        /** Land or shallow water; placed on the highest surface. The stilt shack. */
        SWAMP;

        public static Mode byId(String id) {
            return valueOf(id.toUpperCase(Locale.ROOT));
        }
    }

    public record Column(int surface, int ground) {
        public int depth() {
            return surface - ground;
        }
    }

    /**
     * @param maxSlope    the largest height difference between the dry columns (LAND, SEAFLOOR: ground; SWAMP: surface)
     * @param minDepth    the least water depth at a wet column
     * @param maxDepth    SWAMP: the most water depth at any column
     * @param maxAboveSea LAND: how far the base may stand above the water at the wet columns
     * @param anyWet      LAND: one wet column with water is enough (a lighthouse near the sea), instead of all of them
     * @param yOffset     added to the result: the template layer that sits on the ground, negated
     * @param maxRise     how far the land at the "around" columns may rise above the structure's ground (keeps it out
     *                    of ravines and away from cliffs)
     */
    public record Rules(Mode mode, int maxSlope, int minDepth, int maxDepth, int maxAboveSea, boolean anyWet, int yOffset,
                        int maxRise) {
    }

    /** The y of the template's bottom layer, or empty when the spot does not fit. */
    public static OptionalInt baseY(Rules rules, List<Column> dry, List<Column> wet, List<Column> around, int seaLevel) {
        OptionalInt y = switch (rules.mode()) {
            case LAND -> land(rules, dry, wet, seaLevel);
            case WATER -> water(rules, wet.isEmpty() ? dry : wet);
            case SEAFLOOR -> seafloor(rules, wet.isEmpty() ? dry : wet);
            case SWAMP -> swamp(rules, dry, wet);
        };
        if (y.isEmpty()) {
            return y;
        }
        int ground = y.getAsInt() - rules.yOffset();
        for (Column column : around) {
            if (column.surface() - ground > rules.maxRise()) {
                return OptionalInt.empty();
            }
        }
        return y;
    }

    private static OptionalInt land(Rules rules, List<Column> dry, List<Column> wet, int seaLevel) {
        if (dry.isEmpty() || !deepEnough(rules, wet)) {
            return OptionalInt.empty();
        }
        int lowest = Integer.MAX_VALUE;
        int highest = Integer.MIN_VALUE;
        long sum = 0;
        for (Column column : dry) {
            if (column.depth() > 0 || column.ground() < seaLevel) {
                return OptionalInt.empty();
            }
            lowest = Math.min(lowest, column.ground());
            highest = Math.max(highest, column.ground());
            sum += column.ground();
        }
        if (highest - lowest > rules.maxSlope()) {
            return OptionalInt.empty();
        }
        int y = (int) Math.round((double) sum / dry.size());
        int wetOk = 0;
        for (Column column : wet) {
            boolean ok = column.depth() >= rules.minDepth() && y >= column.surface() && y - column.surface() <= rules.maxAboveSea();
            if (ok) {
                wetOk++;
            } else if (!rules.anyWet()) {
                return OptionalInt.empty();
            }
        }
        if (!wet.isEmpty() && wetOk == 0) {
            return OptionalInt.empty();
        }
        return OptionalInt.of(y + rules.yOffset());
    }

    /**
     * The part of the wet rule that does not depend on the height: water at least {@code minDepth} deep at every wet
     * point (at one, with {@code anyWet}). Checked before the dry points, since most candidate spots fail it and a
     * column is expensive to sample during world generation.
     */
    private static boolean deepEnough(Rules rules, List<Column> wet) {
        if (wet.isEmpty()) {
            return true;
        }
        for (Column column : wet) {
            boolean deep = column.depth() >= rules.minDepth();
            if (deep && rules.anyWet()) {
                return true;
            }
            if (!deep && !rules.anyWet()) {
                return false;
            }
        }
        return !rules.anyWet();
    }

    private static OptionalInt water(Rules rules, List<Column> columns) {
        if (columns.isEmpty()) {
            return OptionalInt.empty();
        }
        int top = Integer.MIN_VALUE;
        int bottom = Integer.MAX_VALUE;
        for (Column column : columns) {
            if (column.depth() < Math.max(1, rules.minDepth())) {
                return OptionalInt.empty();
            }
            top = Math.max(top, column.surface());
            bottom = Math.min(bottom, column.surface());
        }
        // Water surfaces at different heights mean a river running downhill or a lake next to the sea.
        return top - bottom > rules.maxSlope() ? OptionalInt.empty() : OptionalInt.of(top + rules.yOffset());
    }

    private static OptionalInt seafloor(Rules rules, List<Column> columns) {
        if (columns.isEmpty()) {
            return OptionalInt.empty();
        }
        int lowest = Integer.MAX_VALUE;
        int highest = Integer.MIN_VALUE;
        for (Column column : columns) {
            if (column.depth() < rules.minDepth()) {
                return OptionalInt.empty();
            }
            lowest = Math.min(lowest, column.ground());
            highest = Math.max(highest, column.ground());
        }
        return highest - lowest > rules.maxSlope() ? OptionalInt.empty() : OptionalInt.of(lowest + rules.yOffset());
    }

    private static OptionalInt swamp(Rules rules, List<Column> dry, List<Column> wet) {
        int lowest = Integer.MAX_VALUE;
        int highest = Integer.MIN_VALUE;
        int count = 0;
        for (List<Column> list : List.of(dry, wet)) {
            for (Column column : list) {
                if (column.depth() > rules.maxDepth()) {
                    return OptionalInt.empty();
                }
                lowest = Math.min(lowest, column.surface());
                highest = Math.max(highest, column.surface());
                count++;
            }
        }
        if (count == 0 || highest - lowest > rules.maxSlope()) {
            return OptionalInt.empty();
        }
        return OptionalInt.of(highest + rules.yOffset());
    }

    /** Turns a template-local point (x, z) by {@code quarterTurns} clockwise, as vanilla's structure rotation does. */
    public static int[] rotate(int x, int z, int quarterTurns) {
        return switch (Math.floorMod(quarterTurns, 4)) {
            case 1 -> new int[]{-z, x};
            case 2 -> new int[]{-x, -z};
            case 3 -> new int[]{z, -x};
            default -> new int[]{x, z};
        };
    }
}
