package tn.nightbeam.fishermanhouse.fabric;

import java.util.function.Function;
import java.util.function.Supplier;
import net.fabricmc.api.ModInitializer;
import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;
import net.fabricmc.fabric.api.itemgroup.v1.ItemGroupEvents;
import net.fabricmc.fabric.api.loot.v2.LootTableEvents;
import net.fabricmc.loader.api.FabricLoader;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.item.CreativeModeTabs;
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
        ItemGroupEvents.modifyEntriesEvent(CreativeModeTabs.FUNCTIONAL_BLOCKS).register(entries -> ModContent.blockTabItems().forEach(entries::accept));
        ItemGroupEvents.modifyEntriesEvent(CreativeModeTabs.INGREDIENTS).register(entries -> ModContent.ingredientTabItems().forEach(entries::accept));
        CommandRegistrationCallback.EVENT.register((dispatcher, context, environment) -> CoastCommand.register(dispatcher));
        // Rods: one extra pool on vanilla's fishing table, the same as gameplay/rod_extras on the other loaders.
        LootTableEvents.MODIFY.register((resources, lootManager, id, builder, source) -> {
            if (source.isBuiltin() && id.equals(BuiltInLootTables.FISHING)) {
                builder.withPool(LootPool.lootPool()
                        .when(LootItemRandomChanceCondition.randomChance(ModContent.ROD_BOTTLE_CHANCE))
                        .add(LootItem.lootTableItem(ModContent.MESSAGE_IN_A_BOTTLE.get())));
            }
        });
    }

    private static final class FabricRegistrar implements Registrar {
        @Override
        @SuppressWarnings({"unchecked", "rawtypes"})
        public <R, T extends R> Supplier<T> register(ResourceKey<? extends Registry<R>> registry, String path, Function<ResourceLocation, T> factory) {
            ResourceLocation id = FishermanHouse.id(path);
            Registry<R> target = (Registry<R>) BuiltInRegistries.REGISTRY.getOrThrow((ResourceKey) registry);
            T value = factory.apply(id);
            Registry.register(target, id, value);
            return () -> value;
        }
    }
}
