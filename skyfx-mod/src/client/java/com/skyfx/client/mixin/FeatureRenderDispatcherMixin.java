package com.skyfx.client.mixin;

import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

import net.minecraft.client.renderer.feature.FeatureRenderDispatcher;

import com.skyfx.client.render.ItemAuraRenderer;

/** Item aura: the first feature flush after the hand was submitted draws the hand; the outline goes right after it. */
@Mixin(FeatureRenderDispatcher.class)
public abstract class FeatureRenderDispatcherMixin {
	@Inject(method = "renderAllFeatures", at = @At("TAIL"))
	private void skyfx$afterFeatures(CallbackInfo ci) {
		ItemAuraRenderer.afterFeatures();
	}
}
