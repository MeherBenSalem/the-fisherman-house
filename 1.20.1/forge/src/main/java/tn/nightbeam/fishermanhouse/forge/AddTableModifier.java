package tn.nightbeam.fishermanhouse.forge;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import it.unimi.dsi.fastutil.objects.ObjectArrayList;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.storage.loot.LootContext;
import net.minecraft.world.level.storage.loot.LootTable;
import net.minecraft.world.level.storage.loot.predicates.LootItemCondition;
import net.minecraftforge.common.loot.IGlobalLootModifier;
import net.minecraftforge.common.loot.LootModifier;

/** Rolls another loot table into the loot of the tables its conditions match (Forge 1.20.1 has no built-in one). */
public class AddTableModifier extends LootModifier {
    public static final Codec<AddTableModifier> CODEC = RecordCodecBuilder.create(i -> codecStart(i)
            .and(ResourceLocation.CODEC.fieldOf("table").forGetter(m -> m.table))
            .apply(i, AddTableModifier::new));

    private final ResourceLocation table;

    public AddTableModifier(LootItemCondition[] conditions, ResourceLocation table) {
        super(conditions);
        this.table = table;
    }

    @Override
    protected ObjectArrayList<ItemStack> doApply(ObjectArrayList<ItemStack> generatedLoot, LootContext context) {
        LootTable extra = context.getResolver().getLootTable(table);
        extra.getRandomItemsRaw(context, LootTable.createStackSplitter(context.getLevel(), generatedLoot::add));
        return generatedLoot;
    }

    @Override
    public Codec<? extends IGlobalLootModifier> codec() {
        return CODEC;
    }
}
