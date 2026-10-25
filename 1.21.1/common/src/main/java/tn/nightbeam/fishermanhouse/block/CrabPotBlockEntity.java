package tn.nightbeam.fishermanhouse.block;

import java.util.ArrayList;
import java.util.List;
import java.util.stream.IntStream;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.HolderLookup;
import net.minecraft.core.NonNullList;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.FluidTags;
import net.minecraft.tags.TagKey;
import net.minecraft.world.ContainerHelper;
import net.minecraft.world.WorldlyContainer;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.inventory.HopperMenu;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.biome.Biome;
import net.minecraft.world.level.block.entity.BaseContainerBlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.loot.LootParams;
import net.minecraft.world.level.storage.loot.LootTable;
import net.minecraft.world.level.storage.loot.parameters.LootContextParamSets;
import net.minecraft.world.level.storage.loot.parameters.LootContextParams;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.Nullable;
import tn.nightbeam.fishermanhouse.Constants;
import tn.nightbeam.fishermanhouse.FishermanHouse;
import tn.nightbeam.fishermanhouse.content.ModContent;
import tn.nightbeam.fishermanhouse.core.CoastConfig;
import tn.nightbeam.fishermanhouse.core.CrabPotRules;
import tn.nightbeam.fishermanhouse.core.CrabPotRules.Bait;
import tn.nightbeam.fishermanhouse.core.CrabPotRules.Status;

/**
 * Fishes on its own. In enough open water it counts down to the next catch (twice as fast in the rain), then rolls the
 * catch table of the biome it is in, with the luck of its bait, and stores the catch. A catch is only taken when all of
 * it fits, so a full pot waits instead of losing items. Hoppers may put bait in and take everything else out.
 */
public class CrabPotBlockEntity extends BaseContainerBlockEntity implements WorldlyContainer {
    /** Catch tables by biome tag, first match wins; anything else uses {@code gameplay/crab_pot/default}. */
    public static final List<String> PLACES = List.of("frozen", "swamp", "river", "ocean");
    private static final int[] SLOTS = IntStream.range(0, CrabPotRules.SLOTS).toArray();

    private NonNullList<ItemStack> items = NonNullList.withSize(CrabPotRules.SLOTS, ItemStack.EMPTY);
    private int wait = -1;
    private int water;
    private int catches;
    private Status status = Status.NO_WATER;
    private boolean raining;

    public CrabPotBlockEntity(BlockPos pos, BlockState state) {
        super(ModContent.CRAB_POT_ENTITY.get(), pos, state);
    }

    public static boolean isBait(ItemStack stack) {
        return bait(stack) != Bait.NONE;
    }

    public static Bait bait(ItemStack stack) {
        if (stack.isEmpty()) {
            return Bait.NONE;
        }
        var id = BuiltInRegistries.ITEM.getKey(stack.getItem());
        return Constants.MOD_ID.equals(id.getNamespace()) ? Bait.byItemPath(id.getPath()) : Bait.NONE;
    }

    public void serverTick(ServerLevel level, BlockPos pos, BlockState state) {
        CoastConfig.CrabPot config = CoastConfig.get().crabPot();
        if (Math.floorMod(level.getGameTime() + pos.asLong(), 20) == 0) {
            water = state.getValue(CrabPotBlock.WATERLOGGED) ? countWater(level, pos) : 0;
            raining = level.isRaining() && level.isRainingAt(surface(level, pos));
            updateLooks(level, pos, state);
        }
        if (!CrabPotRules.enoughWater(water, config.minWater()) || !state.getValue(CrabPotBlock.WATERLOGGED)) {
            status = Status.NO_WATER;
            return;
        }
        if (wait < 0) {
            wait = CrabPotRules.waitTicks(level.getRandom().nextDouble(), config.minSeconds(), config.maxSeconds(), firstBait());
        }
        if (wait > 0) {
            status = Status.WAITING;
            wait = Math.max(0, wait - CrabPotRules.progress(raining, config.rainBonus()));
            return;
        }
        // Due: a full pot tries again once a second.
        if (Math.floorMod(level.getGameTime() + pos.asLong(), 20) != 0 && status == Status.FULL) {
            return;
        }
        status = tryCatch(level, pos) ? Status.WAITING : Status.FULL;
        if (status == Status.WAITING) {
            wait = -1;
            updateLooks(level, pos, level.getBlockState(pos));
        }
    }

    private boolean tryCatch(ServerLevel level, BlockPos pos) {
        int baitSlot = baitSlot();
        Bait bait = baitSlot < 0 ? Bait.NONE : bait(items.get(baitSlot));
        LootTable table = level.getServer().reloadableRegistries().getLootTable(ResourceKey.create(Registries.LOOT_TABLE,
                FishermanHouse.id("gameplay/crab_pot/" + place(level, pos))));
        LootParams params = new LootParams.Builder(level)
                .withParameter(LootContextParams.ORIGIN, Vec3.atCenterOf(pos))
                .withParameter(LootContextParams.TOOL, new ItemStack(Items.FISHING_ROD))
                .withLuck(bait.luck())
                .create(LootContextParamSets.FISHING);
        List<ItemStack> caught = table.getRandomItems(params);
        NonNullList<ItemStack> after = NonNullList.withSize(CrabPotRules.SLOTS, ItemStack.EMPTY);
        for (int i = 0; i < CrabPotRules.SLOTS; i++) {
            after.set(i, items.get(i).copy());
        }
        if (baitSlot >= 0) {
            after.get(baitSlot).shrink(1);
        }
        for (ItemStack stack : caught) {
            if (!insert(after, stack.copy()).isEmpty()) {
                return false;
            }
        }
        items = after;
        catches++;
        setChanged();
        level.playSound(null, pos, SoundEvents.FISHING_BOBBER_SPLASH, SoundSource.BLOCKS, 0.6F, 0.8F + level.getRandom().nextFloat() * 0.4F);
        BlockPos top = surface(level, pos);
        level.sendParticles(ParticleTypes.BUBBLE_COLUMN_UP, pos.getX() + 0.5, pos.getY() + 0.6, pos.getZ() + 0.5, 12, 0.25, 0.2, 0.25, 0.05);
        level.sendParticles(ParticleTypes.SPLASH, top.getX() + 0.5, top.getY() + 0.1, top.getZ() + 0.5, 16, 0.3, 0.0, 0.3, 0.1);
        level.sendParticles(ParticleTypes.FISHING, top.getX() + 0.5, top.getY() + 0.05, top.getZ() + 0.5, 6, 0.2, 0.0, 0.2, 0.0);
        return true;
    }

    /** Puts as much of {@code stack} as fits into {@code slots}; returns what is left. */
    private static ItemStack insert(NonNullList<ItemStack> slots, ItemStack stack) {
        for (int i = 0; i < slots.size() && !stack.isEmpty(); i++) {
            ItemStack existing = slots.get(i);
            if (!existing.isEmpty() && ItemStack.isSameItemSameComponents(existing, stack)) {
                int move = Math.min(stack.getCount(), existing.getMaxStackSize() - existing.getCount());
                existing.grow(move);
                stack.shrink(move);
            }
        }
        for (int i = 0; i < slots.size() && !stack.isEmpty(); i++) {
            if (slots.get(i).isEmpty()) {
                slots.set(i, stack.split(Math.min(stack.getCount(), stack.getMaxStackSize())));
            }
        }
        return stack;
    }

    /** Adds bait (from a player's hand); returns what did not fit. */
    public ItemStack addBait(ItemStack stack) {
        ItemStack rest = insert(items, stack);
        setChanged();
        if (level instanceof ServerLevel serverLevel) {
            updateLooks(serverLevel, worldPosition, getBlockState());
            serverLevel.playSound(null, worldPosition, SoundEvents.BUNDLE_INSERT, SoundSource.BLOCKS, 0.8F, 1.0F);
        }
        return rest;
    }

    private int baitSlot() {
        for (int i = 0; i < items.size(); i++) {
            if (isBait(items.get(i))) {
                return i;
            }
        }
        return -1;
    }

    private Bait firstBait() {
        int slot = baitSlot();
        return slot < 0 ? Bait.NONE : bait(items.get(slot));
    }

    private void updateLooks(ServerLevel level, BlockPos pos, BlockState state) {
        if (!state.is(ModContent.CRAB_POT.get())) {
            return;
        }
        boolean baited = baitSlot() >= 0;
        boolean caught = items.stream().anyMatch(stack -> !stack.isEmpty() && !isBait(stack));
        if (state.getValue(CrabPotBlock.BAITED) != baited || state.getValue(CrabPotBlock.CAUGHT) != caught) {
            level.setBlock(pos, state.setValue(CrabPotBlock.BAITED, baited).setValue(CrabPotBlock.CAUGHT, caught), 3);
        }
    }

    /** The catch table a pot at this spot uses: the first biome tag that matches, or "default". */
    public static String place(ServerLevel level, BlockPos pos) {
        var biome = level.getBiome(pos);
        for (String place : PLACES) {
            if (biome.is(TagKey.create(Registries.BIOME, FishermanHouse.id("crab_pot/" + place)))) {
                return place;
            }
        }
        return "default";
    }

    private static int countWater(ServerLevel level, BlockPos pos) {
        int count = 0;
        BlockPos.MutableBlockPos cursor = new BlockPos.MutableBlockPos();
        for (int dx = -CrabPotRules.RADIUS; dx <= CrabPotRules.RADIUS; dx++) {
            for (int dy = -1; dy <= 1; dy++) {
                for (int dz = -CrabPotRules.RADIUS; dz <= CrabPotRules.RADIUS; dz++) {
                    if ((dx | dy | dz) != 0 && level.getFluidState(cursor.setWithOffset(pos, dx, dy, dz)).is(FluidTags.WATER)) {
                        count++;
                    }
                }
            }
        }
        return count;
    }

    /** The first block above the water the pot sits in (where rain would fall on it). */
    private static BlockPos surface(ServerLevel level, BlockPos pos) {
        BlockPos.MutableBlockPos cursor = pos.mutable();
        for (int i = 0; i < 32 && level.getFluidState(cursor.above()).is(FluidTags.WATER); i++) {
            cursor.move(Direction.UP);
        }
        return cursor.above();
    }

    /** The action bar line for a sneak-click with an empty hand. */
    public Component statusLine() {
        CoastConfig.CrabPot config = CoastConfig.get().crabPot();
        String key = "status.fisherman_house.crab_pot.";
        Component line = switch (status) {
            case NO_WATER -> Component.translatable(key + "no_water", water, config.minWater()).withStyle(ChatFormatting.RED);
            case FULL -> Component.translatable(key + "full").withStyle(ChatFormatting.GOLD);
            case WAITING -> {
                Bait bait = firstBait();
                Component baitName = bait == Bait.NONE ? Component.translatable(key + "no_bait")
                        : items.get(baitSlot()).getHoverName();
                int ticks = Math.max(0, wait) / CrabPotRules.progress(raining, config.rainBonus());
                yield Component.translatable(key + "waiting", baitName, CrabPotRules.seconds(ticks)).withStyle(ChatFormatting.AQUA);
            }
        };
        if (raining && status == Status.WAITING && config.rainBonus()) {
            line = Component.empty().append(line).append(Component.translatable(key + "rain").withStyle(ChatFormatting.BLUE));
        }
        return line;
    }

    public int catches() {
        return catches;
    }

    @Override
    protected void loadAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.loadAdditional(tag, registries);
        items = NonNullList.withSize(getContainerSize(), ItemStack.EMPTY);
        ContainerHelper.loadAllItems(tag, items, registries);
        wait = tag.contains("Wait") ? tag.getInt("Wait") : -1;
        catches = tag.getInt("Catches");
    }

    @Override
    protected void saveAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.saveAdditional(tag, registries);
        ContainerHelper.saveAllItems(tag, items, registries);
        tag.putInt("Wait", wait);
        tag.putInt("Catches", catches);
    }

    @Override
    public void setChanged() {
        super.setChanged();
        if (level instanceof ServerLevel serverLevel) {
            updateLooks(serverLevel, worldPosition, getBlockState());
        }
    }

    @Override
    protected Component getDefaultName() {
        return Component.translatable("container.fisherman_house.crab_pot");
    }

    @Override
    protected AbstractContainerMenu createMenu(int containerId, Inventory inventory) {
        return new HopperMenu(containerId, inventory, this);
    }

    @Override
    protected NonNullList<ItemStack> getItems() {
        return items;
    }

    @Override
    protected void setItems(NonNullList<ItemStack> items) {
        this.items = items;
    }

    @Override
    public int getContainerSize() {
        return CrabPotRules.SLOTS;
    }

    @Override
    public int[] getSlotsForFace(Direction side) {
        return SLOTS;
    }

    @Override
    public boolean canPlaceItemThroughFace(int slot, ItemStack stack, @Nullable Direction side) {
        return isBait(stack);
    }

    @Override
    public boolean canTakeItemThroughFace(int slot, ItemStack stack, Direction side) {
        return !isBait(stack);
    }

    /** For the inspect command. */
    public List<ItemStack> contents() {
        return new ArrayList<>(items);
    }
}
