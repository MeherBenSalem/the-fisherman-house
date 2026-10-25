package tn.nightbeam.fishermanhouse.forge;

import com.mojang.serialization.Codec;
import java.util.HashMap;
import java.util.Map;
import java.util.function.Function;
import java.util.function.Supplier;
import net.minecraft.core.Registry;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.item.CreativeModeTabs;
import net.minecraftforge.common.MinecraftForge;
import net.minecraftforge.common.loot.IGlobalLootModifier;
import net.minecraftforge.event.BuildCreativeModeTabContentsEvent;
import net.minecraftforge.event.RegisterCommandsEvent;
import net.minecraftforge.eventbus.api.IEventBus;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.fml.javafmlmod.FMLJavaModLoadingContext;
import net.minecraftforge.fml.loading.FMLPaths;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.ForgeRegistries;
import tn.nightbeam.fishermanhouse.Constants;
import tn.nightbeam.fishermanhouse.FishermanHouse;
import tn.nightbeam.fishermanhouse.command.CoastCommand;
import tn.nightbeam.fishermanhouse.content.ModContent;
import tn.nightbeam.fishermanhouse.platform.Registrar;

/** The rod loot is data ({@code data/forge/loot_modifiers}) read by {@link AddTableModifier}. */
@Mod(Constants.MOD_ID)
public final class FishermanHouseForge {
    private final Map<ResourceKey<?>, DeferredRegister<?>> registers = new HashMap<>();

    public FishermanHouseForge() {
        IEventBus modBus = FMLJavaModLoadingContext.get().getModEventBus();
        ModContent.CRAB_POT_FACTORY = ForgeCrabPotBlockEntity::new;
        FishermanHouse.init(FMLPaths.CONFIGDIR::get, new Registrar() {
            @Override
            public <R, T extends R> Supplier<T> register(ResourceKey<? extends Registry<R>> registry, String path, Function<ResourceLocation, T> factory) {
                ResourceLocation id = FishermanHouse.id(path);
                return deferred(registry).register(path, () -> factory.apply(id));
            }
        });
        registers.values().forEach(deferred -> deferred.register(modBus));
        DeferredRegister<Codec<? extends IGlobalLootModifier>> modifiers =
                DeferredRegister.create(ForgeRegistries.Keys.GLOBAL_LOOT_MODIFIER_SERIALIZERS, Constants.MOD_ID);
        modifiers.register("add_table", () -> AddTableModifier.CODEC);
        modifiers.register(modBus);
        modBus.addListener((BuildCreativeModeTabContentsEvent event) -> {
            if (event.getTabKey() == CreativeModeTabs.FUNCTIONAL_BLOCKS) {
                ModContent.blockTabItems().forEach(event::accept);
            } else if (event.getTabKey() == CreativeModeTabs.INGREDIENTS) {
                ModContent.ingredientTabItems().forEach(event::accept);
            }
        });
        MinecraftForge.EVENT_BUS.addListener((RegisterCommandsEvent event) -> CoastCommand.register(event.getDispatcher()));
    }

    @SuppressWarnings("unchecked")
    private <R> DeferredRegister<R> deferred(ResourceKey<? extends Registry<R>> registry) {
        return (DeferredRegister<R>) registers.computeIfAbsent(registry,
                key -> DeferredRegister.create((ResourceKey<? extends Registry<R>>) key, Constants.MOD_ID));
    }
}
