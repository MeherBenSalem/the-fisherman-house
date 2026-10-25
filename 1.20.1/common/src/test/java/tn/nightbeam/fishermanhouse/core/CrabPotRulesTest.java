package tn.nightbeam.fishermanhouse.core;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.junit.jupiter.api.Test;
import tn.nightbeam.fishermanhouse.core.CrabPotRules.Bait;

class CrabPotRulesTest {
    @Test
    void waitIsBetweenMinAndMaxSeconds() {
        assertEquals(1200, CrabPotRules.waitTicks(0.0, 60, 120, Bait.NONE));
        assertEquals(1800, CrabPotRules.waitTicks(0.5, 60, 120, Bait.NONE));
        assertEquals(2400, CrabPotRules.waitTicks(0.9999999, 60, 120, Bait.NONE));
    }

    @Test
    void baitShortensTheWait() {
        assertEquals(600, CrabPotRules.waitTicks(0.0, 60, 120, Bait.FISH_BAIT));
        assertEquals(420, CrabPotRules.waitTicks(0.0, 60, 120, Bait.CHUM));
        assertEquals(1200, CrabPotRules.waitTicks(0.0, 60, 120, Bait.GLOW_BAIT), "glow bait adds luck, not speed");
    }

    @Test
    void waitNeverDropsBelowTheFloorAndSwappedBoundsWork() {
        assertEquals(CrabPotRules.MIN_WAIT_TICKS, CrabPotRules.waitTicks(0.0, 1, 1, Bait.CHUM));
        assertEquals(CrabPotRules.waitTicks(0.3, 60, 120, Bait.NONE), CrabPotRules.waitTicks(0.3, 120, 60, Bait.NONE));
    }

    @Test
    void baitLuckAndIds() {
        assertEquals(0, Bait.FISH_BAIT.luck());
        assertEquals(1, Bait.CHUM.luck());
        assertEquals(3, Bait.GLOW_BAIT.luck());
        assertEquals(Bait.CHUM, Bait.byItemPath("chum"));
        assertEquals(Bait.NONE, Bait.byItemPath("crab_pot"));
        assertEquals(Bait.NONE, Bait.byItemPath(""));
    }

    @Test
    void rainDoublesProgressOnlyWithTheBonus() {
        assertEquals(2, CrabPotRules.progress(true, true));
        assertEquals(1, CrabPotRules.progress(true, false));
        assertEquals(1, CrabPotRules.progress(false, true));
    }

    @Test
    void waterThresholdIsCappedByTheBox() {
        assertTrue(CrabPotRules.enoughWater(20, 20));
        assertFalse(CrabPotRules.enoughWater(19, 20));
        assertTrue(CrabPotRules.enoughWater(CrabPotRules.MAX_WATER, 500));
        assertEquals(74, CrabPotRules.MAX_WATER);
    }

    @Test
    void comparatorAndSeconds() {
        assertEquals(0, CrabPotRules.comparator(0.0, false));
        assertEquals(1, CrabPotRules.comparator(0.01, true));
        assertEquals(15, CrabPotRules.comparator(1.0, true));
        assertEquals(0, CrabPotRules.seconds(0));
        assertEquals(1, CrabPotRules.seconds(1));
        assertEquals(3, CrabPotRules.seconds(41));
    }
}
