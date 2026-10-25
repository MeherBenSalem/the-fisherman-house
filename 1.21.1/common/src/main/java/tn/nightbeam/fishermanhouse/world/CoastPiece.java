package tn.nightbeam.fishermanhouse.world;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.DoubleTag;
import net.minecraft.nbt.ListTag;
import net.minecraft.nbt.Tag;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.ServerLevelAccessor;
import net.minecraft.world.level.StructureManager;
import net.minecraft.world.level.WorldGenLevel;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.Mirror;
import net.minecraft.world.level.block.Rotation;
import net.minecraft.world.level.chunk.ChunkGenerator;
import net.minecraft.world.level.levelgen.structure.BoundingBox;
import net.minecraft.world.level.levelgen.structure.TemplateStructurePiece;
import net.minecraft.world.level.levelgen.structure.pieces.StructurePieceSerializationContext;
import net.minecraft.world.level.levelgen.structure.templatesystem.BlockIgnoreProcessor;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructurePlaceSettings;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructureTemplate;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructureTemplateManager;
import net.minecraft.world.phys.Vec3;
import tn.nightbeam.fishermanhouse.content.ModContent;

/**
 * A placed coastal template. Containers carry their loot tables and residents their trades in the template itself, so
 * the template's entities are placed as they are (not finalized, which would reroll a resident's profession).
 * <p>
 * This version of the game keeps a hanging entity's stored block when it places a template, and then takes the block
 * from the entity's centre: paintings and item frames log "invalid position" and 2x2 paintings move by a block. So the
 * piece places the template's entities itself, hanging ones on their own block, turned with the template.
 */
public class CoastPiece extends TemplateStructurePiece {
    private ListTag entities;

    public CoastPiece(StructureTemplateManager templates, ResourceLocation template, BlockPos origin, Rotation rotation) {
        super(ModContent.COASTAL_PIECE.get(), 0, templates, template, template.toString(), settings(rotation), origin);
    }

    public CoastPiece(StructurePieceSerializationContext context, CompoundTag tag) {
        super(ModContent.COASTAL_PIECE.get(), tag, context.structureTemplateManager(),
                id -> settings(tag.contains("Rot") ? Rotation.valueOf(tag.getString("Rot")) : Rotation.NONE));
    }

    private static StructurePlaceSettings settings(Rotation rotation) {
        return new StructurePlaceSettings()
                .setRotation(rotation)
                .setMirror(Mirror.NONE)
                .setIgnoreEntities(true)
                .addProcessor(BlockIgnoreProcessor.STRUCTURE_BLOCK);
    }

    @Override
    protected void addAdditionalSaveData(StructurePieceSerializationContext context, CompoundTag tag) {
        super.addAdditionalSaveData(context, tag);
        tag.putString("Rot", placeSettings.getRotation().name());
    }

    @Override
    public void postProcess(WorldGenLevel level, StructureManager structures, ChunkGenerator generator, RandomSource random,
                            BoundingBox box, ChunkPos chunk, BlockPos pivot) {
        super.postProcess(level, structures, generator, random, box, chunk, pivot);
        if (entities == null) {
            entities = template.save(new CompoundTag()).getList("entities", Tag.TAG_COMPOUND);
        }
        Rotation rotation = placeSettings.getRotation();
        for (int i = 0; i < entities.size(); i++) {
            CompoundTag info = entities.getCompound(i);
            ListTag b = info.getList("blockPos", Tag.TAG_INT);
            BlockPos block = StructureTemplate.transform(new BlockPos(b.getInt(0), b.getInt(1), b.getInt(2)), Mirror.NONE, rotation,
                    BlockPos.ZERO).offset(templatePosition);
            if (!box.isInside(block)) {
                continue;
            }
            ListTag p = info.getList("pos", Tag.TAG_DOUBLE);
            Vec3 pos = StructureTemplate.transform(new Vec3(p.getDouble(0), p.getDouble(1), p.getDouble(2)), Mirror.NONE, rotation,
                    BlockPos.ZERO).add(templatePosition.getX(), templatePosition.getY(), templatePosition.getZ());
            CompoundTag nbt = info.getCompound("nbt").copy();
            ListTag posTag = new ListTag();
            posTag.add(DoubleTag.valueOf(pos.x));
            posTag.add(DoubleTag.valueOf(pos.y));
            posTag.add(DoubleTag.valueOf(pos.z));
            nbt.put("Pos", posTag);
            nbt.remove("UUID");
            boolean hanging = nbt.contains("TileX");
            if (hanging) {
                nbt.putInt("TileX", block.getX());
                nbt.putInt("TileY", block.getY());
                nbt.putInt("TileZ", block.getZ());
                // Paintings store their side as a horizontal index, item frames as a full direction.
                if (nbt.contains("facing")) {
                    nbt.putByte("facing", (byte) rotation.rotate(Direction.from2DDataValue(nbt.getByte("facing"))).get2DDataValue());
                }
                if (nbt.contains("Facing")) {
                    nbt.putByte("Facing", (byte) rotation.rotate(Direction.from3DDataValue(nbt.getByte("Facing"))).get3DDataValue());
                }
            }
            EntityType.create(nbt, level.getLevel()).ifPresent(entity -> {
                if (!hanging) {
                    float yaw = entity.rotate(rotation) + entity.mirror(Mirror.NONE) - entity.getYRot();
                    entity.moveTo(pos.x, pos.y, pos.z, yaw, entity.getXRot());
                }
                level.addFreshEntityWithPassengers(entity);
            });
        }
    }

    @Override
    protected void handleDataMarker(String marker, BlockPos pos, ServerLevelAccessor level, RandomSource random, BoundingBox box) {
        level.setBlock(pos, Blocks.AIR.defaultBlockState(), Block.UPDATE_CLIENTS);
    }
}
