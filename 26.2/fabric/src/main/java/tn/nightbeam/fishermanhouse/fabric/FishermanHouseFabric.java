package tn.nightbeam.fishermanhouse.fabric;

import java.util.function.Function;
import java.util.function.Supplier;
import net.fabricmc.api.ModInitializer;
import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;
import net.fabricmc.fabric.api.creativetab.v1.CreativeModeTabEvents;
import net.fabricmc.fabric.api.loot.v3.LootTableEvents;
import net.fabricmc.loader.api.FabricLoader;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.Identifier;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.level.storage.loot.BuiltInLootTables;
import net.minecraft.world.level.storage.loot.LootPool;
import net.minecraft.world.level.storage.loot.entries.LootItem;
import net.minecraft.world.level.storage.loot.predicates.LootItemRandomChanceCondition;
import tn.nightbeam.fishermanhouse.FishermanHouse;
import tn.nightbeam.fishermanhouse.command.CoastCommand;
import tn.nightbeam.fishermanhouse.content.ModContent;
import tn.nightbeam.fishermanhouse.platform.Registrar;

public final class FishermanHouseFabric implements ModInitializer {
    @Override
    public void onInitialize() {
        FishermanHouse.init(() -> FabricLoader.getInstance().getConfigDir(), new FabricRegistrar());
        CreativeModeTabEvents.modifyOutputEvent(tab("functional_blocks")).register(output -> ModContent.blockTabItems().forEach(output::accept));
        CreativeModeTabEvents.modifyOutputEvent(tab("ingredients")).register(output -> ModContent.ingredientTabItems().forEach(output::accept));
        CommandRegistrationCallback.EVENT.register((dispatcher, context, environment) -> CoastCommand.register(dispatcher));
        // Rods: one extra pool on vanilla's fishing table, the same as gameplay/rod_extras on the other loaders.
        LootTableEvents.MODIFY.register((key, builder, source, registries) -> {
            if (source.isBuiltin() && key.equals(BuiltInLootTables.FISHING)) {
                builder.withPool(LootPool.lootPool()
                        .when(LootItemRandomChanceCondition.randomChance(ModContent.ROD_BOTTLE_CHANCE))
                        .add(LootItem.lootTableItem(ModContent.MESSAGE_IN_A_BOTTLE.get())));
            }
        });
    }

    private static ResourceKey<CreativeModeTab> tab(String path) {
        return ResourceKey.create(Registries.CREATIVE_MODE_TAB, Identifier.withDefaultNamespace(path));
    }

    private static final class FabricRegistrar implements Registrar {
        @Override
        @SuppressWarnings({"unchecked", "rawtypes"})
        public <R, T extends R> Supplier<T> register(ResourceKey<? extends Registry<R>> registry, String path, Function<Identifier, T> factory) {
            Identifier id = FishermanHouse.id(path);
            Registry<R> target = (Registry<R>) BuiltInRegistries.REGISTRY.getValueOrThrow((ResourceKey) registry);
            T value = factory.apply(id);
            Registry.register(target, id, value);
            return () -> value;
        }
    }
}
