package tn.nightbeam.fishermanhouse.core;

import com.google.gson.JsonObject;
import java.nio.file.Path;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/** {@code config/fisherman_house.json}. Read once at startup; changes apply after a restart. */
public final class CoastConfig {
    public static final String FILE = "fisherman_house.json";
    /** Every structure of the mod, in the order the docs list them. */
    public static final List<String> STRUCTURES = List.of("fisherman_house", "harbour_pier", "lighthouse", "stilt_shack",
            "ice_fishing_camp", "river_boathouse", "sunken_trawler");

    private static volatile Values values = Values.defaults();

    private CoastConfig() {
    }

    public record CrabPot(int minSeconds, int maxSeconds, int minWater, boolean rainBonus) {
    }

    public record Values(CrabPot crabPot, Map<String, Boolean> structures) {
        public static Values defaults() {
            return read(spec().defaults());
        }

        public boolean structureEnabled(String id) {
            return structures.getOrDefault(id, true);
        }
    }

    public static CommentedJson spec() {
        JsonObject structures = new JsonObject();
        STRUCTURES.forEach(id -> structures.addProperty(id, true));
        JsonObject root = Json.obj(
                "crab_pot", Json.obj("min_seconds", 60, "max_seconds", 120, "min_water", 20, "rain_bonus", true),
                "structures", structures);
        return new CommentedJson(root)
                .header("Fisherman's Coast. Changes apply after a restart.\n"
                        + "Biomes, spacing and loot are datapack data: see the README.")
                .comment("crab_pot", "Crab Pots catch something every min_seconds to max_seconds (random in between) when\n"
                        + "unbaited; bait shortens the wait. min_water: water blocks needed in the 5x3x5 box around the pot\n"
                        + "(74 at most). rain_bonus: twice as fast while it rains on the pot.")
                .comment("structures", "Set a structure to false to stop it generating in new chunks (ones already\n"
                        + "generated stay).");
    }

    public static Values read(JsonObject root) {
        int min = clamp(Json.integer(root, "crab_pot.min_seconds", 60), 5, 3600);
        int max = clamp(Json.integer(root, "crab_pot.max_seconds", 120), min, 7200);
        int water = clamp(Json.integer(root, "crab_pot.min_water", 20), 0, CrabPotRules.MAX_WATER);
        boolean rain = Json.bool(root, "crab_pot.rain_bonus", true);
        Map<String, Boolean> structures = new LinkedHashMap<>();
        for (String id : STRUCTURES) {
            structures.put(id, Json.bool(root, "structures." + id, true));
        }
        return new Values(new CrabPot(min, max, water, rain), Map.copyOf(structures));
    }

    public static Values load(Path configDir) {
        values = read(spec().load(configDir.resolve(FILE)));
        return values;
    }

    public static Values get() {
        return values;
    }

    private static int clamp(int value, int min, int max) {
        return Math.max(min, Math.min(max, value));
    }
}
