package tn.nightbeam.fishermanhouse.fabric;

import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.blockrenderlayer.v1.BlockRenderLayerMap;
import net.minecraft.client.renderer.RenderType;
import tn.nightbeam.fishermanhouse.content.ModContent;

/** The net and the pot's netting are see-through. */
public final class FishermanHouseFabricClient implements ClientModInitializer {
    @Override
    public void onInitializeClient() {
        BlockRenderLayerMap.INSTANCE.putBlocks(RenderType.cutout(), ModContent.CRAB_POT.get(), ModContent.FISHING_NET.get());
    }
}
