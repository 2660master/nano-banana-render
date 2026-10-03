package com.skyfx.client.mixin;

import com.llamalad7.mixinextras.injector.wrapoperation.Operation;
import com.llamalad7.mixinextras.injector.wrapoperation.WrapOperation;
import com.mojang.blaze3d.vertex.PoseStack;
import org.spongepowered.asm.mixin.Final;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;

import net.minecraft.client.player.LocalPlayer;
import net.minecraft.client.renderer.GameRenderer;
import net.minecraft.client.renderer.ItemInHandRenderer;
import net.minecraft.client.renderer.RenderBuffers;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.feature.FeatureRenderDispatcher;

import com.skyfx.client.render.ItemAuraRenderer;

/**
 * Item aura: the first-person hand is submitted twice. The first copy is drawn straight away into the aura mask and
 * turned into a glowing outline; the second copy is drawn normally on top of it by vanilla.
 */
@Mixin(GameRenderer.class)
public abstract class GameRendererMixin {
	@Shadow
	@Final
	private FeatureRenderDispatcher featureRenderDispatcher;

	@Shadow
	@Final
	private RenderBuffers renderBuffers;

	@WrapOperation(method = "renderItemInHand", at = @At(value = "INVOKE", target = "Lnet/minecraft/client/renderer/ItemInHandRenderer;renderHandsWithItems(FLcom/mojang/blaze3d/vertex/PoseStack;Lnet/minecraft/client/renderer/SubmitNodeCollector;Lnet/minecraft/client/player/LocalPlayer;I)V"))
	private void skyfx$itemAura(ItemInHandRenderer renderer, float partialTick, PoseStack poseStack, SubmitNodeCollector collector, LocalPlayer player, int light, Operation<Void> original) {
		if (ItemAuraRenderer.shouldRender(player)) {
			original.call(renderer, partialTick, poseStack, collector, player, light);
			ItemAuraRenderer.renderMaskAndGlow(this.featureRenderDispatcher, this.renderBuffers.bufferSource());
		}
		original.call(renderer, partialTick, poseStack, collector, player, light);
	}
}
