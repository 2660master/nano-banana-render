package com.skyfx.client.mixin;

import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

import net.minecraft.client.renderer.SkyRenderer;

import com.skyfx.client.render.SkyFXSkyRenderer;

/**
 * Swaps the vanilla overworld sky for a SkyFX sky. The vanilla sky pass draws the sky disc first and then the sunrise,
 * sun, moon, stars and the dark lower disc; when SkyFX drew its sky, all of those are skipped.
 */
@Mixin(SkyRenderer.class)
public abstract class SkyRendererMixin {
	@Inject(method = "renderSkyDisc", at = @At("HEAD"), cancellable = true)
	private void skyfx$renderCustomSky(CallbackInfo ci) {
		if (SkyFXSkyRenderer.renderSky()) {
			ci.cancel();
		}
	}

	@Inject(method = "renderSunriseAndSunset", at = @At("HEAD"), cancellable = true)
	private void skyfx$skipSunrise(CallbackInfo ci) {
		if (SkyFXSkyRenderer.drewThisFrame()) {
			ci.cancel();
		}
	}

	@Inject(method = "renderSunMoonAndStars", at = @At("HEAD"), cancellable = true)
	private void skyfx$skipCelestials(CallbackInfo ci) {
		if (SkyFXSkyRenderer.drewThisFrame()) {
			ci.cancel();
		}
	}

	@Inject(method = "renderDarkDisc", at = @At("HEAD"), cancellable = true)
	private void skyfx$skipDarkDisc(CallbackInfo ci) {
		if (SkyFXSkyRenderer.drewThisFrame()) {
			ci.cancel();
		}
	}
}
