package tn.nightbeam.fishermanhouse.neoforge;

import java.util.HashMap;
import java.util.Map;
import java.util.function.Function;
import java.util.function.Supplier;
import net.minecraft.core.Direction;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.item.CreativeModeTab;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.fml.common.Mod;
import net.neoforged.fml.loading.FMLPaths;
import net.neoforged.neoforge.capabilities.Capabilities;
import net.neoforged.neoforge.capabilities.RegisterCapabilitiesEvent;
import net.neoforged.neoforge.common.NeoForge;
import net.neoforged.neoforge.event.BuildCreativeModeTabContentsEvent;
import net.neoforged.neoforge.event.RegisterCommandsEvent;
import net.neoforged.neoforge.registries.DeferredRegister;
import net.neoforged.neoforge.items.wrapper.SidedInvWrapper;
import tn.nightbeam.fishermanhouse.Constants;
import tn.nightbeam.fishermanhouse.FishermanHouse;
import tn.nightbeam.fishermanhouse.command.CoastCommand;
import tn.nightbeam.fishermanhouse.content.ModContent;
import tn.nightbeam.fishermanhouse.platform.Registrar;

/** The rod loot is data: {@code neoforge:add_table} in {@code data/fisherman_house/loot_modifiers}. */
@Mod(Constants.MOD_ID)
public final class FishermanHouseNeoForge {
    private static final ResourceKey<CreativeModeTab> FUNCTIONAL_BLOCKS = tab("functional_blocks");
    private static final ResourceKey<CreativeModeTab> INGREDIENTS = tab("ingredients");

    private final Map<ResourceKey<?>, DeferredRegister<?>> registers = new HashMap<>();

    public FishermanHouseNeoForge(IEventBus modBus) {
        FishermanHouse.init(FMLPaths.CONFIGDIR::get, new Registrar() {
            @Override
            public <R, T extends R> Supplier<T> register(ResourceKey<? extends Registry<R>> registry, String path, Function<ResourceLocation, T> factory) {
                return deferred(registry).register(path, factory);
            }
        });
        registers.values().forEach(deferred -> deferred.register(modBus));
        modBus.addListener((BuildCreativeModeTabContentsEvent event) -> {
            if (event.getTabKey() == FUNCTIONAL_BLOCKS) {
                ModContent.blockTabItems().forEach(event::accept);
            } else if (event.getTabKey() == INGREDIENTS) {
                ModContent.ingredientTabItems().forEach(event::accept);
            }
        });
        modBus.addListener((RegisterCapabilitiesEvent event) ->
                event.registerBlockEntity(Capabilities.ItemHandler.BLOCK, ModContent.CRAB_POT_ENTITY.get(),
                        (pot, side) -> new SidedInvWrapper(pot, side == null ? Direction.UP : side)));
        NeoForge.EVENT_BUS.addListener((RegisterCommandsEvent event) -> CoastCommand.register(event.getDispatcher()));
    }

    private static ResourceKey<CreativeModeTab> tab(String path) {
        return ResourceKey.create(Registries.CREATIVE_MODE_TAB, ResourceLocation.withDefaultNamespace(path));
    }

    @SuppressWarnings("unchecked")
    private <R> DeferredRegister<R> deferred(ResourceKey<? extends Registry<R>> registry) {
        return (DeferredRegister<R>) registers.computeIfAbsent(registry,
                key -> DeferredRegister.create((ResourceKey<? extends Registry<R>>) key, Constants.MOD_ID));
    }
}
