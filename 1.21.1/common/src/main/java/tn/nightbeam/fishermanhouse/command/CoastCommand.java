package tn.nightbeam.fishermanhouse.command;

import com.mojang.brigadier.CommandDispatcher;
import com.mojang.brigadier.context.CommandContext;
import com.mojang.brigadier.exceptions.CommandSyntaxException;
import java.util.Map;
import java.util.TreeMap;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.commands.arguments.coordinates.BlockPosArgument;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.npc.Villager;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.trading.MerchantOffer;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.RandomizableContainerBlockEntity;
import net.minecraft.world.level.levelgen.structure.BoundingBox;
import net.minecraft.world.level.levelgen.structure.Structure;
import net.minecraft.world.level.levelgen.structure.StructureStart;
import net.minecraft.world.phys.AABB;
import tn.nightbeam.fishermanhouse.Constants;
import tn.nightbeam.fishermanhouse.block.CrabPotBlockEntity;
import tn.nightbeam.fishermanhouse.content.ModContent;

/**
 * {@code /fishermanscoast inspect [pos] [fill]} and {@code inspect area <from> <to> [fill]} (operators): what a
 * coastal structure holds. One line per structure: its box, its containers by loot table, its residents (name, number
 * of trades, whether they sell Crab Pots), its Crab Pots and Fishing Nets. {@code fill} rolls the containers' loot first
 * and counts stacks and maps. Meant for datapack makers and the QA scripts.
 */
public final class CoastCommand {
    public static final String NAME = "fishermanscoast";

    private CoastCommand() {
    }

    public static void register(CommandDispatcher<CommandSourceStack> dispatcher) {
        dispatcher.register(Commands.literal(NAME)
                .requires(source -> source.hasPermission(2))
                .then(Commands.literal("inspect")
                        .executes(c -> inspect(c, BlockPos.containing(c.getSource().getPosition()), false))
                        .then(Commands.literal("area")
                                .then(Commands.argument("from", BlockPosArgument.blockPos())
                                        .then(Commands.argument("to", BlockPosArgument.blockPos())
                                                .executes(c -> area(c, false))
                                                .then(Commands.literal("fill").executes(c -> area(c, true))))))
                        .then(Commands.argument("pos", BlockPosArgument.blockPos())
                                .executes(c -> inspect(c, BlockPosArgument.getLoadedBlockPos(c, "pos"), false))
                                .then(Commands.literal("fill")
                                        .executes(c -> inspect(c, BlockPosArgument.getLoadedBlockPos(c, "pos"), true))))));
    }

    private static int inspect(CommandContext<CommandSourceStack> context, BlockPos pos, boolean fill) {
        CommandSourceStack source = context.getSource();
        ServerLevel level = source.getLevel();
        int found = 0;
        for (Map.Entry<ResourceKey<Structure>, Structure> entry : level.registryAccess().registryOrThrow(Registries.STRUCTURE).entrySet()) {
            if (!entry.getKey().location().getNamespace().equals(Constants.MOD_ID)) {
                continue;
            }
            StructureStart start = startAt(level, pos, entry.getValue());
            if (start != null) {
                report(source, entry.getKey().location().getPath(), start.getBoundingBox(), fill);
                found++;
            }
        }
        if (found == 0) {
            source.sendFailure(Component.literal("FC inspect none: no Fisherman's Coast structure at " + pos.toShortString()));
        }
        return found;
    }

    /** A box regardless of structure data: /place structure places blocks without recording a structure. */
    private static int area(CommandContext<CommandSourceStack> context, boolean fill) throws CommandSyntaxException {
        BoundingBox box = BoundingBox.fromCorners(BlockPosArgument.getBlockPos(context, "from"), BlockPosArgument.getBlockPos(context, "to"));
        report(context.getSource(), "area", box, fill);
        return 1;
    }

    private static void report(CommandSourceStack source, String label, BoundingBox box, boolean fill) {
        ServerLevel level = source.getLevel();
        Map<String, Integer> containers = new TreeMap<>();
        Map<String, Integer> residents = new TreeMap<>();
        Map<String, Integer> potPlaces = new TreeMap<>();
        int stacks = 0;
        int maps = 0;
        int pots = 0;
        int nets = 0;
        for (int cx = box.minX() >> 4; cx <= box.maxX() >> 4; cx++) {
            for (int cz = box.minZ() >> 4; cz <= box.maxZ() >> 4; cz++) {
                if (!level.hasChunk(cx, cz)) {
                    continue;
                }
                for (BlockEntity be : level.getChunk(cx, cz).getBlockEntities().values()) {
                    if (!box.isInside(be.getBlockPos())) {
                        continue;
                    }
                    if (be instanceof RandomizableContainerBlockEntity container) {
                        String table = container.getLootTable() == null ? "none" : container.getLootTable().location().toString();
                        if (fill) {
                            container.unpackLootTable(null);
                            for (int i = 0; i < container.getContainerSize(); i++) {
                                ItemStack stack = container.getItem(i);
                                stacks += stack.isEmpty() ? 0 : 1;
                                maps += stack.is(Items.FILLED_MAP) ? 1 : 0;
                            }
                        }
                        containers.merge(table, 1, Integer::sum);
                    } else if (be instanceof CrabPotBlockEntity) {
                        pots++;
                        potPlaces.merge(CrabPotBlockEntity.place(level, be.getBlockPos()), 1, Integer::sum);
                    }
                }
            }
        }
        for (BlockPos pos : BlockPos.betweenClosed(box.minX(), box.minY(), box.minZ(), box.maxX(), box.maxY(), box.maxZ())) {
            if (level.isLoaded(pos) && level.getBlockState(pos).is(ModContent.FISHING_NET.get())) {
                nets++;
            }
        }
        for (Villager villager : level.getEntitiesOfClass(Villager.class, AABB.of(box).inflate(4))) {
            String name = villager.hasCustomName() ? villager.getCustomName().getString().replace(' ', '_') : "unnamed";
            boolean sellsPots = false;
            for (MerchantOffer offer : villager.getOffers()) {
                sellsPots |= offer.getResult().is(ModContent.CRAB_POT_ITEM.get());
            }
            residents.merge(name + "[" + villager.getOffers().size() + (sellsPots ? ",pots" : "") + "]", 1, Integer::sum);
        }
        String line = String.format("FC inspect id=%s box=%d,%d,%d,%d,%d,%d containers=%s residents=%s pots=%d pot_tables=%s nets=%d%s",
                label, box.minX(), box.minY(), box.minZ(), box.maxX(), box.maxY(), box.maxZ(),
                join(containers), join(residents), pots, join(potPlaces), nets, fill ? " stacks=" + stacks + " maps=" + maps : "");
        source.sendSuccess(() -> Component.literal(line), false);
    }

    /** The structure with a piece at {@code pos} or in the columns around it (so a /locate result can be inspected). */
    private static StructureStart startAt(ServerLevel level, BlockPos pos, Structure structure) {
        StructureStart start = level.structureManager().getStructureWithPieceAt(pos, structure);
        for (int dx = -16; dx <= 16 && !start.isValid(); dx += 4) {
            for (int dz = -16; dz <= 16 && !start.isValid(); dz += 4) {
                for (int y = level.getMinBuildHeight(); !start.isValid() && y < level.getMaxBuildHeight(); y += 4) {
                    start = level.structureManager().getStructureWithPieceAt(new BlockPos(pos.getX() + dx, y, pos.getZ() + dz), structure);
                }
            }
        }
        return start.isValid() ? start : null;
    }

    private static String join(Map<String, Integer> counts) {
        if (counts.isEmpty()) {
            return "-";
        }
        StringBuilder out = new StringBuilder();
        counts.forEach((key, count) -> out.append(out.isEmpty() ? "" : ",").append(key).append('*').append(count));
        return out.toString();
    }
}
