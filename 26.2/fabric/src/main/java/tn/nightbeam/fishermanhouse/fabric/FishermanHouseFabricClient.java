package tn.nightbeam.fishermanhouse.fabric;

import net.fabricmc.api.ClientModInitializer;

/** Nothing to set up on the client: the net and the pot's netting are cut out by their textures' transparency. */
public final class FishermanHouseFabricClient implements ClientModInitializer {
    @Override
    public void onInitializeClient() {
    }
}
