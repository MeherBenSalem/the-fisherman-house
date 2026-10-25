package tn.nightbeam.fishermanhouse.block;

import com.mojang.serialization.MapCodec;
import net.minecraft.world.level.block.LadderBlock;

/** A net that hangs on a wall like a ladder: climbable (block tag), waterloggable, see-through. */
public class FishingNetBlock extends LadderBlock {
    private static final MapCodec<LadderBlock> CODEC = simpleCodec(FishingNetBlock::new);

    public FishingNetBlock(Properties properties) {
        super(properties);
    }

    @Override
    public MapCodec<LadderBlock> codec() {
        return CODEC;
    }
}
