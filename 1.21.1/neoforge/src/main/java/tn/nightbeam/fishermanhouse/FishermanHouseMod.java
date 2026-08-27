package tn.nightbeam.fishermanhouse;

import net.neoforged.bus.api.IEventBus;
import net.neoforged.fml.common.Mod;

@Mod(Constants.MOD_ID)
public class FishermanHouseMod {

    public FishermanHouseMod(IEventBus eventBus) {
        FishermanHouse.init();
    }
}
