package tn.nightbeam.fishermanhouse.core;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

class CoastConfigTest {
    @TempDir
    Path dir;

    @Test
    void firstStartWritesACommentedFileWithDefaults() throws Exception {
        CoastConfig.Values values = CoastConfig.load(dir);
        String text = Files.readString(dir.resolve(CoastConfig.FILE), StandardCharsets.UTF_8);
        assertTrue(text.startsWith("// Fisherman's Coast."), text);
        assertTrue(text.contains("\"rain_bonus\": true"));
        assertEquals(60, values.crabPot().minSeconds());
        assertEquals(120, values.crabPot().maxSeconds());
        assertEquals(20, values.crabPot().minWater());
        CoastConfig.STRUCTURES.forEach(id -> assertTrue(values.structureEnabled(id), id));
    }

    @Test
    void userValuesWinAndBadValuesAreClamped() throws Exception {
        Files.writeString(dir.resolve(CoastConfig.FILE), """
                // edited
                {"crab_pot": {"min_seconds": 1, "max_seconds": 2, "min_water": 900, "rain_bonus": false},
                 "structures": {"lighthouse": false}, "extra": 5}
                """);
        CoastConfig.Values values = CoastConfig.load(dir);
        assertEquals(5, values.crabPot().minSeconds());
        assertEquals(5, values.crabPot().maxSeconds(), "never below the minimum");
        assertEquals(CrabPotRules.MAX_WATER, values.crabPot().minWater());
        assertFalse(values.crabPot().rainBonus());
        assertFalse(values.structureEnabled("lighthouse"));
        assertTrue(values.structureEnabled("harbour_pier"));
        assertTrue(Files.readString(dir.resolve(CoastConfig.FILE)).contains("\"extra\": 5"), "unknown keys are kept");
    }

    @Test
    void brokenFileFallsBackToDefaultsAndIsLeftAlone() throws Exception {
        Files.writeString(dir.resolve(CoastConfig.FILE), "{ not json");
        CoastConfig.Values values = CoastConfig.load(dir);
        assertEquals(60, values.crabPot().minSeconds());
        assertEquals("{ not json", Files.readString(dir.resolve(CoastConfig.FILE)));
    }
}
