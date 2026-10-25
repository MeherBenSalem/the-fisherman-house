package tn.nightbeam.fishermanhouse.world;

import net.minecraft.core.BlockPos;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.DoubleTag;
import net.minecraft.nbt.ListTag;
import net.minecraft.resources.Identifier;
import net.minecraft.util.ProblemReporter;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.EntitySpawnReason;
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
import net.minecraft.world.level.storage.TagValueInput;
import net.minecraft.world.phys.Vec3;
import tn.nightbeam.fishermanhouse.content.ModContent;

/**
 * A placed coastal template. Containers carry their loot tables and residents their trades in the template itself, so
 * the template's entities are placed as they are (not finalized, which would reroll a resident's profession).
 * <p>
 * This version of the game keeps a hanging entity's stored block when it places a template, so paintings and item
 * frames log "invalid position" and lose their place. The piece places the template's entities itself, moving that
 * block along with the entity as later versions of the game do.
 */
public class CoastPiece extends TemplateStructurePiece {
    private ListTag entities;

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
            entities = template.save(new CompoundTag()).getListOrEmpty("entities");
        }
        Rotation rotation = placeSettings.getRotation();
        for (int i = 0; i < entities.size(); i++) {
            CompoundTag info = entities.getCompoundOrEmpty(i);
            ListTag b = info.getListOrEmpty("blockPos");
            BlockPos block = StructureTemplate.transform(new BlockPos(b.getIntOr(0, 0), b.getIntOr(1, 0), b.getIntOr(2, 0)), Mirror.NONE,
                    rotation, BlockPos.ZERO).offset(templatePosition);
            if (!box.isInside(block)) {
                continue;
            }
            ListTag p = info.getListOrEmpty("pos");
            Vec3 pos = StructureTemplate.transform(new Vec3(p.getDoubleOr(0, 0), p.getDoubleOr(1, 0), p.getDoubleOr(2, 0)), Mirror.NONE,
                    rotation, BlockPos.ZERO).add(templatePosition.getX(), templatePosition.getY(), templatePosition.getZ());
            CompoundTag nbt = info.getCompoundOrEmpty("nbt").copy();
            ListTag posTag = new ListTag();
            posTag.add(DoubleTag.valueOf(pos.x));
            posTag.add(DoubleTag.valueOf(pos.y));
            posTag.add(DoubleTag.valueOf(pos.z));
            nbt.put("Pos", posTag);
            nbt.remove("UUID");
            if (nbt.contains("block_pos")) {
                nbt.store("block_pos", BlockPos.CODEC, block);
            }
            EntityType.create(TagValueInput.create(ProblemReporter.DISCARDING, level.registryAccess(), nbt), level.getLevel(),
                    EntitySpawnReason.STRUCTURE).ifPresent(entity -> {
                float yaw = entity.rotate(rotation) + entity.mirror(Mirror.NONE) - entity.getYRot();
                entity.snapTo(pos.x, pos.y, pos.z, yaw, entity.getXRot());
                entity.setYBodyRot(yaw);
                entity.setYHeadRot(yaw);
                level.addFreshEntityWithPassengers(entity);
            });
        }
    }

    @Override
    protected void handleDataMarker(String marker, BlockPos pos, ServerLevelAccessor level, RandomSource random, BoundingBox box) {
        level.setBlock(pos, Blocks.AIR.defaultBlockState(), Block.UPDATE_CLIENTS);
    }
}
