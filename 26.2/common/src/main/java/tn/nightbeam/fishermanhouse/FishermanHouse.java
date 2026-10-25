package tn.nightbeam.fishermanhouse;

import net.minecraft.resources.Identifier;
import tn.nightbeam.fishermanhouse.content.ModContent;
import tn.nightbeam.fishermanhouse.core.CoastConfig;
import tn.nightbeam.fishermanhouse.platform.Platform;
import tn.nightbeam.fishermanhouse.platform.Registrar;

/** Common entry point, called by each loader's mod class. */
public final class FishermanHouse {
    private FishermanHouse() {
    }

    public static void init(Platform platform, Registrar registrar) {
        CoastConfig.load(platform.configDir());
        ModContent.register(registrar);
        Constants.LOG.info("{} ready: {} structures enabled", Constants.MOD_NAME,
                CoastConfig.STRUCTURES.stream().filter(CoastConfig.get()::structureEnabled).count());
    }

    public static Identifier id(String path) {
        return Identifier.fromNamespaceAndPath(Constants.MOD_ID, path);
    }
}
