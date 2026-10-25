package tn.nightbeam.fishermanhouse.world;

import com.mojang.serialization.Codec;
import com.mojang.serialization.MapCodec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.OptionalInt;
import net.minecraft.core.BlockPos;
import net.minecraft.resources.Identifier;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.block.Rotation;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.levelgen.structure.Structure;
import net.minecraft.world.level.levelgen.structure.StructureType;
import tn.nightbeam.fishermanhouse.content.ModContent;
import tn.nightbeam.fishermanhouse.core.CoastConfig;
import tn.nightbeam.fishermanhouse.core.Shore;

/**
 * One template placed where the shore suits it. Before anything is placed, the land around the chunk is sampled (before
 * features, with and without water) at the template's "dry" and "wet" points for each rotation and a few positions
 * around the chunk's middle; the first combination {@link Shore} accepts is used, so docks point into the water and
 * land parts stand on level ground. Everything is set in the structure's JSON, so datapacks can add more.
 *
 * <pre>
 * "type": "fisherman_house:coastal", "template": "fisherman_house:harbour_pier", "config_name": "harbour_pier",
 * "site": {"mode": "land", "max_slope": 2, "min_depth": 3, "max_above_sea": 4, "y_offset": -4},
 * "anchor": [4, 4], "dry": [[1, 1], [7, 7]], "wet": [[4, 30]], "around": [[-6, 4]], "search": 1
 * </pre>
 */
public class CoastStructure extends Structure {
    private static final Codec<List<Integer>> POINT = Codec.INT.listOf().validate(p -> p.size() == 2
            ? com.mojang.serialization.DataResult.success(p) : com.mojang.serialization.DataResult.error(() -> "a point is [x, z]"));
    private static final Codec<Shore.Rules> RULES = RecordCodecBuilder.create(i -> i.group(
            Codec.STRING.xmap(Shore.Mode::byId, mode -> mode.name().toLowerCase(java.util.Locale.ROOT)).fieldOf("mode").forGetter(Shore.Rules::mode),
            Codec.INT.optionalFieldOf("max_slope", 2).forGetter(Shore.Rules::maxSlope),
            Codec.INT.optionalFieldOf("min_depth", 0).forGetter(Shore.Rules::minDepth),
            Codec.INT.optionalFieldOf("max_depth", 64).forGetter(Shore.Rules::maxDepth),
            Codec.INT.optionalFieldOf("max_above_sea", 4).forGetter(Shore.Rules::maxAboveSea),
            Codec.BOOL.optionalFieldOf("any_wet", false).forGetter(Shore.Rules::anyWet),
            Codec.INT.optionalFieldOf("y_offset", 0).forGetter(Shore.Rules::yOffset),
            Codec.INT.optionalFieldOf("max_rise", 64).forGetter(Shore.Rules::maxRise)
    ).apply(i, Shore.Rules::new));
    public static final MapCodec<CoastStructure> CODEC = RecordCodecBuilder.mapCodec(i -> i.group(
            settingsCodec(i),
            Identifier.CODEC.fieldOf("template").forGetter(s -> s.template),
            Codec.STRING.optionalFieldOf("config_name", "").forGetter(s -> s.configName),
            RULES.fieldOf("site").forGetter(s -> s.rules),
            POINT.fieldOf("anchor").forGetter(s -> s.anchor),
            POINT.listOf().optionalFieldOf("dry", List.of()).forGetter(s -> s.dry),
            POINT.listOf().optionalFieldOf("wet", List.of()).forGetter(s -> s.wet),
            POINT.listOf().optionalFieldOf("around", List.of()).forGetter(s -> s.around),
            Codec.intRange(0, 3).optionalFieldOf("search", 1).forGetter(s -> s.search)
    ).apply(i, CoastStructure::new));

    private final Identifier template;
    private final String configName;
    private final Shore.Rules rules;
    private final List<Integer> anchor;
    private final List<List<Integer>> dry;
    private final List<List<Integer>> wet;
    private final List<List<Integer>> around;
    private final int search;

    public CoastStructure(StructureSettings settings, Identifier template, String configName, Shore.Rules rules, List<Integer> anchor,
                          List<List<Integer>> dry, List<List<Integer>> wet, List<List<Integer>> around, int search) {
        super(settings);
        this.template = template;
        this.configName = configName;
        this.rules = rules;
        this.anchor = anchor;
        this.dry = dry;
        this.wet = wet;
        this.around = around;
        this.search = search;
    }

    @Override
    public Optional<GenerationStub> findGenerationPoint(GenerationContext context) {
        if (!configName.isEmpty() && !CoastConfig.get().structureEnabled(configName)) {
            return Optional.empty();
        }
        RandomSource random = context.random();
        ChunkPos chunk = context.chunkPos();
        int seaLevel = context.chunkGenerator().getSeaLevel();
        Map<Long, Shore.Column> columns = new HashMap<>();
        List<int[]> spots = new ArrayList<>();
        for (int dx = -search; dx <= search; dx++) {
            for (int dz = -search; dz <= search; dz++) {
                spots.add(new int[]{chunk.getMiddleBlockX() + dx * 8, chunk.getMiddleBlockZ() + dz * 8});
            }
        }
        shuffle(spots, random);
        List<Rotation> rotations = new ArrayList<>(List.of(Rotation.values()));
        for (int[] spot : spots) {
            if (!biomeFits(context, new BlockPos(spot[0], seaLevel, spot[1]))) {
                continue;
            }
            shuffle(rotations, random);
            for (Rotation rotation : rotations) {
                int turns = rotation.ordinal();
                int[] a = Shore.rotate(anchor.get(0), anchor.get(1), turns);
                int originX = spot[0] - a[0];
                int originZ = spot[1] - a[1];
                OptionalInt y = Shore.baseY(rules, sample(context, columns, dry, originX, originZ, turns),
                        sample(context, columns, wet, originX, originZ, turns),
                        sample(context, columns, around, originX, originZ, turns), seaLevel);
                if (y.isEmpty()) {
                    continue;
                }
                BlockPos origin = new BlockPos(originX, y.getAsInt(), originZ);
                BlockPos centre = new BlockPos(spot[0], y.getAsInt() - rules.yOffset(), spot[1]);
                return Optional.of(new GenerationStub(centre, pieces -> pieces.addPiece(
                        new CoastPiece(context.structureTemplateManager(), template, origin, rotation))));
            }
        }
        return Optional.empty();
    }

    private static boolean biomeFits(GenerationContext context, BlockPos pos) {
        return context.isValidBiome(new GenerationStub(pos, pieces -> { }));
    }

    private static List<Shore.Column> sample(GenerationContext context, Map<Long, Shore.Column> cache, List<List<Integer>> points,
                                             int originX, int originZ, int turns) {
        List<Shore.Column> out = new ArrayList<>(points.size());
        for (List<Integer> point : points) {
            int[] p = Shore.rotate(point.get(0), point.get(1), turns);
            int x = originX + p[0];
            int z = originZ + p[1];
            out.add(cache.computeIfAbsent(BlockPos.asLong(x, 0, z), key -> new Shore.Column(
                    context.chunkGenerator().getFirstOccupiedHeight(x, z, Heightmap.Types.WORLD_SURFACE_WG, context.heightAccessor(), context.randomState()),
                    context.chunkGenerator().getFirstOccupiedHeight(x, z, Heightmap.Types.OCEAN_FLOOR_WG, context.heightAccessor(), context.randomState()))));
        }
        return out;
    }

    private static <T> void shuffle(List<T> list, RandomSource random) {
        for (int i = list.size() - 1; i > 0; i--) {
            int j = random.nextInt(i + 1);
            T swap = list.get(i);
            list.set(i, list.get(j));
            list.set(j, swap);
        }
    }

    @Override
    public StructureType<?> type() {
        return ModContent.COASTAL.get();
    }
}
