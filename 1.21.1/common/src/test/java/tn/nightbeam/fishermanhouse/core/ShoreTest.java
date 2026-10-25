package tn.nightbeam.fishermanhouse.core;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.List;
import org.junit.jupiter.api.Test;
import tn.nightbeam.fishermanhouse.core.Shore.Column;
import tn.nightbeam.fishermanhouse.core.Shore.Mode;
import tn.nightbeam.fishermanhouse.core.Shore.Rules;

class ShoreTest {
    private static final int SEA = 63;
    private static final Rules PIER = new Rules(Mode.LAND, 2, 3, 64, 4, false, -4, 64);

    private static Column dry(int y) {
        return new Column(y, y);
    }

    private static Column water(int floor) {
        return new Column(SEA, floor);
    }

    @Test
    void landPartOnLevelBeachWithDeepWaterAhead() {
        var y = Shore.baseY(PIER, List.of(dry(64), dry(65), dry(64), dry(65)), List.of(water(58), water(57)), List.of(), SEA);
        // Average 64.5 rounds to 65 (half up), then the template's ground layer (4) is subtracted.
        assertEquals(61, y.getAsInt());
    }

    @Test
    void dockPointingInlandIsRejected() {
        assertTrue(Shore.baseY(PIER, List.of(dry(64), dry(64)), List.of(dry(64), water(58)), List.of(), SEA).isEmpty());
    }

    @Test
    void wetPointsAreCheckedBeforeTheDryOnes() {
        // A dry point that would fail on its own is never read when the water ahead is too shallow.
        var dry = new java.util.AbstractList<Column>() {
            @Override
            public Column get(int index) {
                throw new AssertionError("dry point read");
            }

            @Override
            public int size() {
                return 1;
            }
        };
        assertTrue(Shore.baseY(PIER, dry, List.of(water(61)), List.of(), SEA).isEmpty());
        Rules anyWet = new Rules(Mode.LAND, 2, 3, 64, 4, true, -4, 64);
        assertTrue(Shore.baseY(anyWet, dry, List.of(water(61), dry(64)), List.of(), SEA).isEmpty());
        assertEquals(60, Shore.baseY(anyWet, List.of(dry(64)), List.of(dry(64), water(58)), List.of(), SEA).getAsInt());
    }

    @Test
    void shallowWaterIsNotEnoughForAPier() {
        assertTrue(Shore.baseY(PIER, List.of(dry(64)), List.of(water(61)), List.of(), SEA).isEmpty());
    }

    @Test
    void landPartMustBeDryLevelAndAboveTheSea() {
        assertTrue(Shore.baseY(PIER, List.of(dry(64), water(62)), List.of(water(55)), List.of(), SEA).isEmpty(), "water under the house");
        assertTrue(Shore.baseY(PIER, List.of(dry(64), dry(68)), List.of(water(55)), List.of(), SEA).isEmpty(), "too steep");
        assertTrue(Shore.baseY(PIER, List.of(dry(60), dry(60)), List.of(water(55)), List.of(), SEA).isEmpty(), "below sea level");
    }

    @Test
    void aCliffTooHighAboveTheWaterIsRejected() {
        assertTrue(Shore.baseY(PIER, List.of(dry(72), dry(72)), List.of(water(55)), List.of(), SEA).isEmpty());
        assertTrue(Shore.baseY(PIER, List.of(dry(67), dry(67)), List.of(water(55)), List.of(), SEA).isPresent());
    }

    @Test
    void lighthouseNeedsWaterOnOneSideOnly() {
        Rules lighthouse = new Rules(Mode.LAND, 2, 2, 64, 6, true, 0, 64);
        assertTrue(Shore.baseY(lighthouse, List.of(dry(66)), List.of(dry(66), dry(67), water(59)), List.of(), SEA).isPresent());
        assertTrue(Shore.baseY(lighthouse, List.of(dry(66)), List.of(dry(66), dry(67), dry(66)), List.of(), SEA).isEmpty());
    }

    @Test
    void iceCampSitsOnTheWaterSurface() {
        Rules camp = new Rules(Mode.WATER, 0, 2, 64, 0, false, -1, 64);
        assertEquals(62, Shore.baseY(camp, List.of(), List.of(water(50), water(55)), List.of(), SEA).getAsInt());
        assertTrue(Shore.baseY(camp, List.of(), List.of(water(50), dry(64)), List.of(), SEA).isEmpty());
    }

    @Test
    void wreckLiesOnTheLowestFloorOfDeepWater() {
        Rules wreck = new Rules(Mode.SEAFLOOR, 4, 10, 64, 0, false, -1, 64);
        assertEquals(44, Shore.baseY(wreck, List.of(), List.of(water(45), water(47), water(48)), List.of(), SEA).getAsInt());
        assertTrue(Shore.baseY(wreck, List.of(), List.of(water(45), water(56)), List.of(), SEA).isEmpty(), "too shallow");
        assertTrue(Shore.baseY(wreck, List.of(), List.of(water(40), water(46)), List.of(), SEA).isEmpty(), "too uneven");
    }

    @Test
    void stiltShackTakesLandOrShallowWater() {
        Rules shack = new Rules(Mode.SWAMP, 2, 0, 3, 0, false, -5, 4);
        assertEquals(59, Shore.baseY(shack, List.of(dry(64), water(61)), List.of(), List.of(), SEA).getAsInt());
        assertTrue(Shore.baseY(shack, List.of(dry(64), water(55)), List.of(), List.of(), SEA).isEmpty(), "deep water");
    }

    @Test
    void cliffsAroundTheSpotAreRejected() {
        Rules shack = new Rules(Mode.SWAMP, 2, 0, 3, 0, false, -5, 4);
        var footprint = List.of(dry(64), water(61));
        assertEquals(59, Shore.baseY(shack, footprint, List.of(), List.of(dry(66), water(60), dry(68)), SEA).getAsInt());
        assertTrue(Shore.baseY(shack, footprint, List.of(), List.of(dry(66), dry(70)), SEA).isEmpty(), "a cliff beside it");
    }

    @Test
    void rotationMatchesVanillaClockwiseTurns() {
        assertArrayEquals(new int[]{3, 5}, Shore.rotate(3, 5, 0));
        assertArrayEquals(new int[]{-5, 3}, Shore.rotate(3, 5, 1));
        assertArrayEquals(new int[]{-3, -5}, Shore.rotate(3, 5, 2));
        assertArrayEquals(new int[]{5, -3}, Shore.rotate(3, 5, 3));
        assertArrayEquals(new int[]{3, 5}, Shore.rotate(3, 5, 4));
    }
}
