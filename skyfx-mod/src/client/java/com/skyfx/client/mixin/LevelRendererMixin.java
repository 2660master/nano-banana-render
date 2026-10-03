package com.skyfx.client.mixin;

import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

import net.minecraft.client.renderer.LevelRenderer;

import com.skyfx.client.config.SkyFXConfig;
import com.skyfx.client.render.SkyFXSkyRenderer;

/** Optionally hides the blocky vanilla clouds while a SkyFX sky (which has its own clouds) is active. */
@Mixin(LevelRenderer.class)
public abstract class LevelRendererMixin {
	@Inject(method = "addCloudsPass", at = @At("HEAD"), cancellable = true)
	private void skyfx$hideVanillaClouds(CallbackInfo ci) {
		if (SkyFXConfig.get().hideVanillaClouds && SkyFXSkyRenderer.isCustomSkySelected()) {
			ci.cancel();
		}
	}
}
