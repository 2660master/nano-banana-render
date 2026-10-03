package com.skyfx.client.render;

import java.util.OptionalInt;

import com.mojang.blaze3d.buffers.GpuBufferSlice;
import com.mojang.blaze3d.pipeline.BlendFunction;
import com.mojang.blaze3d.pipeline.RenderPipeline;
import com.mojang.blaze3d.pipeline.RenderTarget;
import com.mojang.blaze3d.platform.DepthTestFunction;
import com.mojang.blaze3d.shaders.UniformType;
import com.mojang.blaze3d.systems.GpuDevice;
import com.mojang.blaze3d.systems.RenderPass;
import com.mojang.blaze3d.systems.RenderSystem;
import com.mojang.blaze3d.textures.FilterMode;
import com.mojang.blaze3d.textures.GpuTexture;
import com.mojang.blaze3d.textures.GpuTextureView;
import com.mojang.blaze3d.textures.TextureFormat;
import com.mojang.blaze3d.vertex.DefaultVertexFormat;
import com.mojang.blaze3d.vertex.VertexFormat;
import org.joml.Matrix4f;
import org.joml.Vector3f;
import org.joml.Vector4f;
import org.jspecify.annotations.Nullable;

import net.minecraft.client.Minecraft;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.feature.FeatureRenderDispatcher;
import net.minecraft.resources.Identifier;
import net.minecraft.util.Util;

import com.skyfx.client.SkyFXClient;
import com.skyfx.client.config.SkyFXConfig;

/**
 * Item aura: a glowing outline around the item(s) held in first person.
 *
 * <p>The hand is drawn one extra time into an off-screen mask texture; a full-screen shader then paints a crisp outline
 * and a soft glow just outside the silhouette onto the screen, before the hand is drawn normally on top.
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

	/** Same usage flags vanilla uses for its picture-in-picture GUI textures (render attachment + sampled). */
	private static final int USAGE_COLOR = 12;
	private static final int USAGE_DEPTH = 8;

	private static @Nullable GpuTexture maskColor;
	private static @Nullable GpuTexture maskDepth;
	private static @Nullable GpuTextureView maskColorView;
	private static @Nullable GpuTextureView maskDepthView;
	private static boolean reportedInvalid;
	private static int reportedFrames;

	private ItemAuraRenderer() {
	}

	public static boolean shouldRender(@Nullable LocalPlayer player) {
		return SkyFXConfig.get().itemAuraEnabled && player != null
				&& (!player.getMainHandItem().isEmpty() || !player.getOffhandItem().isEmpty());
	}

	/**
	 * Called right after the hand was submitted for an extra mask pass: draws the submitted hand into the mask,
	 * then composites the outline onto the main target.
	 */
	public static void renderMaskAndGlow(FeatureRenderDispatcher dispatcher, MultiBufferSource.BufferSource buffers) {
		if (!RenderSystem.getDevice().precompilePipeline(PIPELINE).isValid()) {
			if (!reportedInvalid) {
				reportedInvalid = true;
				SkyFXClient.LOGGER.error("SkyFX item aura shader failed to compile, item aura disabled");
			}
			dispatcher.renderAllFeatures();
			buffers.endBatch();
			return;
		}
		if (reportedFrames < 3) {
			reportedFrames++;
			int items = 0;
			for (var collection : dispatcher.getSubmitNodeStorage().getSubmitsPerOrder().values()) {
				items += collection.getItemSubmits().size();
			}
			SkyFXClient.LOGGER.info("SkyFX item aura active, {} item(s) in the mask pass, model view {}", items, RenderSystem.getModelViewMatrix());
		}
		RenderTarget main = Minecraft.getInstance().getMainRenderTarget();
		ensureMask(main.width, main.height);

		RenderSystem.getDevice().createCommandEncoder().clearColorAndDepthTextures(maskColor, 0, maskDepth, 1.0);
		RenderSystem.outputColorTextureOverride = maskColorView;
		RenderSystem.outputDepthTextureOverride = maskDepthView;
		try {
			dispatcher.renderAllFeatures();
			buffers.endBatch();
		} finally {
			RenderSystem.outputColorTextureOverride = null;
			RenderSystem.outputDepthTextureOverride = null;
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
			pass.bindTexture("InSampler", maskColorView, RenderSystem.getSamplerCache().getClampToEdge(FilterMode.LINEAR));
			pass.draw(0, 3);
		}
	}

	private static void ensureMask(int width, int height) {
		if (maskColor != null && maskColor.getWidth(0) == width && maskColor.getHeight(0) == height) {
			return;
		}
		if (maskColor != null) {
			maskColorView.close();
			maskColor.close();
			maskDepthView.close();
			maskDepth.close();
		}
		GpuDevice device = RenderSystem.getDevice();
		maskColor = device.createTexture(() -> "SkyFX item aura mask", USAGE_COLOR, TextureFormat.RGBA8, width, height, 1, 1);
		maskColorView = device.createTextureView(maskColor);
		maskDepth = device.createTexture(() -> "SkyFX item aura mask depth", USAGE_DEPTH, TextureFormat.DEPTH32, width, height, 1, 1);
		maskDepthView = device.createTextureView(maskDepth);
	}
}
