package com.skyfx.client.mixin;

import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

import net.minecraft.client.renderer.GameRenderer;

import com.skyfx.client.render.ItemAuraRenderer;

/** Item aura: remembers that the first-person hand (with an item) was submitted this frame. */
@Mixin(GameRenderer.class)
public abstract class GameRendererMixin {
	@Inject(method = "renderItemInHand", at = @At(value = "INVOKE", target = "Lnet/minecraft/client/renderer/ItemInHandRenderer;renderHandsWithItems(FLcom/mojang/blaze3d/vertex/PoseStack;Lnet/minecraft/client/renderer/SubmitNodeCollector;Lnet/minecraft/client/player/LocalPlayer;I)V", shift = At.Shift.AFTER))
	private void skyfx$handSubmitted(CallbackInfo ci) {
		ItemAuraRenderer.onHandSubmitted(net.minecraft.client.Minecraft.getInstance().player);
	}
}
