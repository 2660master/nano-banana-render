package com.skyfx.client.mixin;

import org.joml.Vector4f;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

import net.minecraft.client.Camera;
import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.fog.FogRenderer;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.level.material.FogType;

import com.skyfx.client.render.SkyFXSkyRenderer;

/** Tints the distance fog with the horizon colour of the SkyFX sky, so far-away terrain melts into the sky. */
@Mixin(FogRenderer.class)
public abstract class FogRendererMixin {
	@Inject(method = "computeFogColor", at = @At("RETURN"))
	private void skyfx$matchSkyFog(CallbackInfoReturnable<Vector4f> cir) {
		float[] fog = SkyFXSkyRenderer.fogColor();
		if (fog == null) return;
		Camera camera = Minecraft.getInstance().gameRenderer.getMainCamera();
		FogType fluid = camera.getFluidInCamera();
		if (fluid == FogType.WATER || fluid == FogType.LAVA || fluid == FogType.POWDER_SNOW) return;
		if (camera.entity() instanceof LivingEntity living && (living.hasEffect(MobEffects.BLINDNESS) || living.hasEffect(MobEffects.DARKNESS))) return;
		Vector4f color = cir.getReturnValue();
		color.set(fog[0], fog[1], fog[2], color.w);
	}
}
