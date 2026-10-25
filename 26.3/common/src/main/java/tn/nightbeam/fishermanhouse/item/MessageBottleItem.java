package tn.nightbeam.fishermanhouse.item;

import net.minecraft.ChatFormatting;
import net.minecraft.advancements.triggers.CriteriaTriggers;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.stats.Stats;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.storage.loot.LootParams;
import net.minecraft.world.level.storage.loot.LootTable;
import net.minecraft.world.level.storage.loot.parameters.LootContextParamSets;
import net.minecraft.world.level.storage.loot.parameters.LootContextParams;
import tn.nightbeam.fishermanhouse.FishermanHouse;

/**
 * Breaks open: one of the notes is read out and the bottle's loot table ({@code gameplay/message_in_a_bottle}) is
 * rolled for the player: a small treasure or a map to the nearest Sunken Trawler.
 */
public class MessageBottleItem extends Item {
    public static final int NOTES = 12;
    public static final ResourceKey<LootTable> TABLE = ResourceKey.create(Registries.LOOT_TABLE, FishermanHouse.id("gameplay/message_in_a_bottle"));

    public MessageBottleItem(Properties properties) {
        super(properties);
    }

    @Override
    public InteractionResult use(Level level, Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (level instanceof ServerLevel serverLevel && player instanceof ServerPlayer serverPlayer) {
            open(serverLevel, serverPlayer, stack);
            stack.consume(1, player);
        }
        return InteractionResult.SUCCESS;
    }

    private static void open(ServerLevel level, ServerPlayer player, ItemStack stack) {
        int note = level.getRandom().nextInt(NOTES);
        player.sendSystemMessage(Component.translatable("item.fisherman_house.message_in_a_bottle.reads",
                Component.translatable("item.fisherman_house.message_in_a_bottle.note." + note)
                        .withStyle(ChatFormatting.ITALIC, ChatFormatting.AQUA)).withStyle(ChatFormatting.GRAY));
        LootParams params = new LootParams.Builder(level)
                .withParameter(LootContextParams.ORIGIN, player.position())
                .withParameter(LootContextParams.THIS_ENTITY, player)
                .withLuck(player.getLuck())
                .create(LootContextParamSets.GIFT);
        for (ItemStack loot : level.getServer().reloadableRegistries().getLootTable(TABLE).getRandomItems(params)) {
            if (!player.getInventory().add(loot)) {
                level.addFreshEntity(new ItemEntity(level, player.getX(), player.getY(), player.getZ(), loot));
            }
        }
        level.playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.SPLASH_POTION_BREAK, SoundSource.PLAYERS, 0.7F, 1.2F);
        level.sendParticles(ParticleTypes.SPLASH, player.getX(), player.getEyeY() - 0.3, player.getZ(), 20, 0.3, 0.2, 0.3, 0.1);
        CriteriaTriggers.CONSUME_ITEM.trigger(player, stack);
        player.awardStat(Stats.ITEM_USED.get(stack.getItem()));
    }
}
