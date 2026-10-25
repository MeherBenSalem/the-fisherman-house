package tn.nightbeam.fishermanhouse.forge;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraftforge.common.capabilities.Capability;
import net.minecraftforge.common.capabilities.ForgeCapabilities;
import net.minecraftforge.common.util.LazyOptional;
import net.minecraftforge.items.IItemHandlerModifiable;
import net.minecraftforge.items.wrapper.SidedInvWrapper;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;
import tn.nightbeam.fishermanhouse.block.CrabPotBlockEntity;

/**
 * Forge's container block entities hand hoppers an unsided item handler, which would ignore the pot's rules (only
 * bait goes in, bait never comes out); this one hands out the sided view instead.
 */
public class ForgeCrabPotBlockEntity extends CrabPotBlockEntity {
    private final LazyOptional<IItemHandlerModifiable>[] handlers = SidedInvWrapper.create(this, Direction.values());

    public ForgeCrabPotBlockEntity(BlockPos pos, BlockState state) {
        super(pos, state);
    }

    @Override
    public <T> @NotNull LazyOptional<T> getCapability(@NotNull Capability<T> cap, @Nullable Direction side) {
        if (cap == ForgeCapabilities.ITEM_HANDLER && !remove) {
            return handlers[(side == null ? Direction.UP : side).ordinal()].cast();
        }
        return super.getCapability(cap, side);
    }

    @Override
    public void invalidateCaps() {
        super.invalidateCaps();
        for (LazyOptional<IItemHandlerModifiable> handler : handlers) {
            handler.invalidate();
        }
    }
}
