package com.skyfx.client.render;

import java.util.OptionalInt;

import com.mojang.blaze3d.buffers.GpuBufferSlice;
import com.mojang.blaze3d.pipeline.BlendFunction;
import com.mojang.blaze3d.pipeline.RenderPipeline;
import com.mojang.blaze3d.pipeline.RenderTarget;
import com.mojang.blaze3d.platform.DepthTestFunction;
import com.mojang.blaze3d.shaders.UniformType;
import com.mojang.blaze3d.systems.RenderPass;
import com.mojang.blaze3d.systems.RenderSystem;
import com.mojang.blaze3d.textures.FilterMode;
import com.mojang.blaze3d.vertex.DefaultVertexFormat;
import com.mojang.blaze3d.vertex.VertexFormat;
import org.joml.Matrix4f;
import org.joml.Vector3f;
import org.joml.Vector4f;
import org.jspecify.annotations.Nullable;

import net.minecraft.client.Minecraft;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.resources.Identifier;
import net.minecraft.util.Util;

import com.skyfx.client.SkyFXClient;
import com.skyfx.client.config.SkyFXConfig;

/**
 * Item aura: a glowing outline around the item(s) held in first person.
 *
 * <p>Vanilla clears the main depth buffer right before it draws the first-person hand, so once the hand is drawn the
 * depth buffer holds exactly its silhouette. A full-screen shader reads that depth and paints a crisp outline and a
 * soft glow just outside it. No extra render of the hand is needed.
 */
public final class ItemAuraRenderer {
	private static final RenderPipeline PIPELINE = RenderPipeline.builder()
			.withLocation(Identifier.fromNamespaceAndPath(SkyFXClient.MOD_ID, "pipeline/item_aura"))
			.withVertexShader("core/screenquad")
			.withFragmentShader(Identifier.fromNamespaceAndPath(SkyFXClient.MOD_ID, "core/item_aura"))
			.withSampler("InSampler")
			.withUniform("DynamicTransforms", UniformType.UNIFORM_BUFFER)
			.withUniform("Globals", UniformType.UNIFORM_BUFFER)
			.withBlend(BlendFunction.TRANSLUCENT)
			.withDepthWrite(false)
			.withDepthTestFunction(DepthTestFunction.NO_DEPTH_TEST)
			.withColorWrite(true, false)
			.withVertexFormat(DefaultVertexFormat.EMPTY, VertexFormat.Mode.TRIANGLES)
			.build();

	/** Set when this frame's hand (with an item) was submitted; the outline is drawn once that hand has been drawn. */
	private static boolean handSubmitted;
	private static boolean reportedInvalid;
	private static boolean reportedActive;

	private ItemAuraRenderer() {
	}

	public static boolean shouldRender(@Nullable LocalPlayer player) {
		return SkyFXConfig.get().itemAuraEnabled && player != null
				&& (!player.getMainHandItem().isEmpty() || !player.getOffhandItem().isEmpty());
	}

	/** Called when vanilla submits the first-person hand. */
	public static void onHandSubmitted(@Nullable LocalPlayer player) {
		handSubmitted = shouldRender(player);
	}

	/**
	 * Called after every {@code FeatureRenderDispatcher.renderAllFeatures()}. The first call after the hand was
	 * submitted is the one that draws it: flush it, then paint the outline around its silhouette in the depth buffer.
	 */
	public static void afterFeatures() {
		if (!handSubmitted) return;
		handSubmitted = false;
		Minecraft minecraft = Minecraft.getInstance();
		minecraft.renderBuffers().bufferSource().endBatch();
		if (!RenderSystem.getDevice().precompilePipeline(PIPELINE).isValid()) {
			if (!reportedInvalid) {
				reportedInvalid = true;
				SkyFXClient.LOGGER.error("SkyFX item aura shader failed to compile, item aura disabled");
			}
			return;
		}
		RenderTarget main = minecraft.getMainRenderTarget();
		if (main.getDepthTextureView() == null) return;
		if (!reportedActive) {
			reportedActive = true;
			SkyFXClient.LOGGER.info("SkyFX item aura active");
		}

		SkyFXConfig config = SkyFXConfig.get();
		float seconds = (Util.getMillis() % 3_600_000L) / 1000.0F;
		int rgb = config.itemAuraRainbow ? AuraRenderer.hsvToRgb((seconds * 0.12F) % 1.0F, 0.75F, 1.0F) : config.itemAuraColor;
		float scale = Math.max(1.0F, main.height / 540.0F);
		GpuBufferSlice transforms = RenderSystem.getDynamicUniforms().writeTransform(
				new Matrix4f(),
				new Vector4f(((rgb >> 16) & 0xFF) / 255.0F, ((rgb >> 8) & 0xFF) / 255.0F, (rgb & 0xFF) / 255.0F,
						Boolean.getBoolean("skyfx.debugItemMask") ? -1.0F : 1.0F),
				new Vector3f(config.itemAuraWidth * scale, config.itemAuraGlow * 2.0F * scale, seconds),
				new Matrix4f());
		try (RenderPass pass = RenderSystem.getDevice().createCommandEncoder().createRenderPass(
				() -> "SkyFX item aura", main.getColorTextureView(), OptionalInt.empty())) {
			pass.setPipeline(PIPELINE);
			RenderSystem.bindDefaultUniforms(pass);
			pass.setUniform("DynamicTransforms", transforms);
			pass.bindTexture("InSampler", main.getDepthTextureView(), RenderSystem.getSamplerCache().getClampToEdge(FilterMode.NEAREST));
			pass.draw(0, 3);
		}
	}
}
