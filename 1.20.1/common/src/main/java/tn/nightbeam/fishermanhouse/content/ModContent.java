package tn.nightbeam.fishermanhouse.content;

import java.util.List;
import java.util.function.Supplier;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.Rarity;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.levelgen.structure.StructureType;
import net.minecraft.world.level.levelgen.structure.pieces.StructurePieceType;
import net.minecraft.world.level.material.MapColor;
import tn.nightbeam.fishermanhouse.block.CrabPotBlock;
import tn.nightbeam.fishermanhouse.block.CrabPotBlockEntity;
import tn.nightbeam.fishermanhouse.block.FishingNetBlock;
import tn.nightbeam.fishermanhouse.item.MessageBottleItem;
import tn.nightbeam.fishermanhouse.platform.Registrar;
import tn.nightbeam.fishermanhouse.world.CoastPiece;
import tn.nightbeam.fishermanhouse.world.CoastStructure;

/** Everything the mod registers. */
public final class ModContent {
    /** The chance that a rod's catch comes with a Message in a Bottle (also in data/.../gameplay/rod_extras.json). */
    public static final float ROD_BOTTLE_CHANCE = 0.015F;
    public static Supplier<Block> CRAB_POT;
    public static Supplier<Block> FISHING_NET;
    public static Supplier<Item> CRAB_POT_ITEM;
    public static Supplier<Item> FISHING_NET_ITEM;
    public static Supplier<Item> FISH_BAIT;
    public static Supplier<Item> CHUM;
    public static Supplier<Item> GLOW_BAIT;
    public static Supplier<Item> MESSAGE_IN_A_BOTTLE;
    public static Supplier<BlockEntityType<CrabPotBlockEntity>> CRAB_POT_ENTITY;
    /** Forge swaps in a block entity that hands hoppers the sided view of the pot. */
    public static BlockEntityType.BlockEntitySupplier<CrabPotBlockEntity> CRAB_POT_FACTORY = CrabPotBlockEntity::new;
    public static Supplier<StructureType<CoastStructure>> COASTAL;
    public static Supplier<StructurePieceType> COASTAL_PIECE;

    private ModContent() {
    }

    public static void register(Registrar r) {
        CRAB_POT = r.register(Registries.BLOCK, "crab_pot", id -> new CrabPotBlock(block(id)
                .mapColor(MapColor.WOOD).strength(1.0F).sound(SoundType.WOOD).noOcclusion()));
        FISHING_NET = r.register(Registries.BLOCK, "fishing_net", id -> new FishingNetBlock(block(id)
                .mapColor(MapColor.WOOL).strength(0.4F).sound(SoundType.WOOL).noOcclusion()));
        CRAB_POT_ITEM = r.register(Registries.ITEM, "crab_pot", id -> new BlockItem(CRAB_POT.get(), item(id)));
        FISHING_NET_ITEM = r.register(Registries.ITEM, "fishing_net", id -> new BlockItem(FISHING_NET.get(), item(id)));
        FISH_BAIT = r.register(Registries.ITEM, "fish_bait", id -> new Item(item(id)));
        CHUM = r.register(Registries.ITEM, "chum", id -> new Item(item(id)));
        GLOW_BAIT = r.register(Registries.ITEM, "glow_bait", id -> new Item(item(id).rarity(Rarity.UNCOMMON)));
        MESSAGE_IN_A_BOTTLE = r.register(Registries.ITEM, "message_in_a_bottle", id -> new MessageBottleItem(item(id)
                .stacksTo(16).rarity(Rarity.UNCOMMON)));
        CRAB_POT_ENTITY = r.register(Registries.BLOCK_ENTITY_TYPE, "crab_pot",
                id -> BlockEntityType.Builder.of(CRAB_POT_FACTORY, CRAB_POT.get()).build(null));
        COASTAL = r.register(Registries.STRUCTURE_TYPE, "coastal", id -> () -> CoastStructure.CODEC);
        COASTAL_PIECE = r.register(Registries.STRUCTURE_PIECE, "coastal_piece", id -> CoastPiece::new);
    }

    /** Blocks for the Functional Blocks tab. */
    public static List<Item> blockTabItems() {
        return List.of(CRAB_POT_ITEM.get(), FISHING_NET_ITEM.get());
    }

    /** Items for the Ingredients tab. */
    public static List<Item> ingredientTabItems() {
        return List.of(FISH_BAIT.get(), CHUM.get(), GLOW_BAIT.get(), MESSAGE_IN_A_BOTTLE.get());
    }

    private static Item.Properties item(ResourceLocation id) {
        return new Item.Properties();
    }

    private static BlockBehaviour.Properties block(ResourceLocation id) {
        return BlockBehaviour.Properties.of();
    }
}
