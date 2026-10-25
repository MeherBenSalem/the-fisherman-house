package tn.nightbeam.fishermanhouse.world;

import net.minecraft.core.BlockPos;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.resources.Identifier;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.ServerLevelAccessor;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.Mirror;
import net.minecraft.world.level.block.Rotation;
import net.minecraft.world.level.levelgen.structure.BoundingBox;
import net.minecraft.world.level.levelgen.structure.TemplateStructurePiece;
import net.minecraft.world.level.levelgen.structure.pieces.StructurePieceSerializationContext;
import net.minecraft.world.level.levelgen.structure.templatesystem.BlockIgnoreProcessor;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructurePlaceSettings;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructureTemplateManager;
import tn.nightbeam.fishermanhouse.content.ModContent;

/**
 * A placed coastal template. Containers carry their loot tables and residents their trades in the template itself, so
 * the template's entities are placed as they are (not finalized, which would reroll a resident's profession).
 */
public class CoastPiece extends TemplateStructurePiece {
    public CoastPiece(StructureTemplateManager templates, Identifier template, BlockPos origin, Rotation rotation) {
        super(ModContent.COASTAL_PIECE.get(), 0, templates, template, template.toString(), settings(rotation), origin);
    }

    public CoastPiece(StructurePieceSerializationContext context, CompoundTag tag) {
        super(ModContent.COASTAL_PIECE.get(), tag, context.structureTemplateManager(),
                id -> settings(Rotation.valueOf(tag.getStringOr("Rot", "NONE"))));
    }

    private static StructurePlaceSettings settings(Rotation rotation) {
        return new StructurePlaceSettings()
                .setRotation(rotation)
                .setMirror(Mirror.NONE)
                .addProcessor(BlockIgnoreProcessor.STRUCTURE_BLOCK);
    }

    @Override
    protected void addAdditionalSaveData(StructurePieceSerializationContext context, CompoundTag tag) {
        super.addAdditionalSaveData(context, tag);
        tag.putString("Rot", placeSettings.getRotation().name());
    }

    @Override
    protected void handleDataMarker(String marker, BlockPos pos, ServerLevelAccessor level, RandomSource random, BoundingBox box) {
        level.setBlock(pos, Blocks.AIR.defaultBlockState(), Block.UPDATE_CLIENTS);
    }
}
